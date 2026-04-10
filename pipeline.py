import os
import json
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv
import chromadb

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma = chromadb.PersistentClient(path="data/vectordb")
coleccion = chroma.get_or_create_collection(name="presupuestos")

def extraer(ruta_pdf):
    paginas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for numero, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text()
            tablas = pagina.extract_tables()
            paginas.append({
                "pagina": numero + 1,
                "fuente": ruta_pdf,
                "texto": texto if texto else "",
                "tablas": tablas if tablas else [],
                "tipo": "texto" if texto else "imagen_sin_texto"
            })
    return paginas

def chunkear(paginas):
    TAMANO = 500
    SOLAPE = 50
    chunks = []

    for pagina in paginas:
        numero = pagina["pagina"]
        fuente = pagina["fuente"]

        if pagina["texto"]:
            palabras = pagina["texto"].split()
            inicio = 0
            while inicio < len(palabras):
                fin = inicio + TAMANO
                texto_chunk = " ".join(palabras[inicio:fin])
                chunks.append({
                    "texto": texto_chunk,
                    "pagina": numero,
                    "fuente": fuente,
                    "tipo": "texto"
                })
                inicio += TAMANO - SOLAPE

        for tabla in pagina["tablas"]:
            if not tabla or not tabla[0]:
                continue
            cabeceras = tabla[0]
            lineas = []
            for fila in tabla[1:]:
                if not any(fila):
                    continue
                partes = []
                for i, celda in enumerate(fila):
                    if celda and i < len(cabeceras) and cabeceras[i]:
                        cab = str(cabeceras[i]).replace("\n", " ").strip()
                        val = str(celda).replace("\n", " ").strip()
                        partes.append(f"{cab}: {val}")
                if partes:
                    lineas.append(" | ".join(partes))
            if lineas:
                chunks.append({
                    "texto": "\n".join(lineas),
                    "pagina": numero,
                    "fuente": fuente,
                    "tipo": "tabla"
                })

    return chunks

def vectorizar(chunks, fuente):
    existentes = coleccion.get(where={"fuente": fuente})
    if existentes and len(existentes["ids"]) > 0:
        print(f"   Ya existe en la base de datos — saltando")
        return

    for i, chunk in enumerate(chunks):
        if not chunk["texto"].strip():
            continue
        respuesta = client.embeddings.create(
            input=chunk["texto"],
            model="text-embedding-3-small"
        )
        vector = respuesta.data[0].embedding
        id_unico = f"{fuente}_chunk_{i}"
        coleccion.add(
            ids=[id_unico],
            embeddings=[vector],
            documents=[chunk["texto"]],
            metadatas=[{
                "pagina": chunk["pagina"],
                "fuente": chunk["fuente"],
                "tipo": chunk["tipo"]
            }]
        )
        print(f"   chunk {i+1}/{len(chunks)} vectorizado")

RUTA_JSON = "data/processed/datos_extraidos.json"

def cargar_json_existente():
    if os.path.exists(RUTA_JSON):
        with open(RUTA_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def fuentes_en_json(datos):
    return {entrada["fuente"] for entrada in datos}

def guardar_json(datos):
    with open(RUTA_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def procesar_pdf(ruta_pdf, datos_json, fuentes_procesadas):
    print(f"\nProcesando: {ruta_pdf}")

    if ruta_pdf in fuentes_procesadas:
        print(f"   Ya está en datos_extraidos.json — saltando extracción")
        paginas = [e for e in datos_json if e["fuente"] == ruta_pdf]
    else:
        print(f"Extrayendo texto y tablas...")
        paginas = extraer(ruta_pdf)
        datos_json.extend(paginas)
        guardar_json(datos_json)
        fuentes_procesadas.add(ruta_pdf)
        print(f"   {len(paginas)} páginas añadidas a datos_extraidos.json")

    print(f"Generando chunks...")
    chunks = chunkear(paginas)
    print(f"Chunks generados: {len(chunks)}")

    print(f"Vectorizando y subiendo a ChromaDB...")
    vectorizar(chunks, ruta_pdf)
    print(f"Listo.")

def main():
    pdfs = [f for f in os.listdir("data/raw") if f.endswith(".pdf")]

    if not pdfs:
        print("No hay PDFs en data/raw/")
        return

    datos_json = cargar_json_existente()
    fuentes_procesadas = fuentes_en_json(datos_json)
    print(f"PDFs en datos_extraidos.json: {len(fuentes_procesadas)}")

    print(f"PDFs encontrados en data/raw: {len(pdfs)}")
    nuevos = [f for f in pdfs if f"data/raw/{f}" not in fuentes_procesadas]
    print(f"PDFs nuevos a procesar: {len(nuevos)}")

    for pdf in pdfs:
        ruta = f"data/raw/{pdf}"
        procesar_pdf(ruta, datos_json, fuentes_procesadas)

    total = coleccion.count()
    print(f"\nPipeline completado.")
    print(f"Total páginas en datos_extraidos.json: {len(datos_json)}")
    print(f"Total vectores en base de datos: {total}")

main()
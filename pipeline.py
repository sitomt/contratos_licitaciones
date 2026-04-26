import os
import json
import time
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv
import chromadb
from src.normalizador import normalizar_texto

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma = chromadb.PersistentClient(path="data/vectordb")
coleccion = chroma.get_or_create_collection(name="presupuestos")

MODELO_NARRATIVIZADOR = "gpt-4o"
PAUSA_ENTRE_LLAMADAS = 0.5
MAX_COLUMNAS_TABLA = 15
RUTA_JSON = "data/processed/datos_extraidos.json"


def extraer(ruta_pdf):
    paginas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for numero, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text()
            tablas_raw = pagina.extract_tables()

            tablas_limpias = []
            for tabla in (tablas_raw or []):
                filas_validas = [
                    fila for fila in tabla
                    if any(c for c in fila if c and str(c).strip())
                ]
                if len(filas_validas) < 2:
                    continue
                if len(filas_validas[0]) > MAX_COLUMNAS_TABLA:
                    continue
                tablas_limpias.append(filas_validas)

            paginas.append({
                "pagina": numero + 1,
                "fuente": ruta_pdf,
                "texto": texto if texto else "",
                "tablas": tablas_limpias,
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
        texto_pagina = pagina["texto"]

        if texto_pagina:
            palabras = texto_pagina.split()
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
                    "tipo": "tabla",
                    "texto_pagina": texto_pagina
                })

    return chunks


def narrativizar_tabla(texto_tabla, pagina, fuente, texto_pagina=""):
    prompt = f"""Eres un redactor de documentos oficiales de presupuestos públicos españoles.
Tienes delante los datos de una tabla extraída de un documento presupuestario oficial y el texto de la página donde aparece esa tabla.

TEXTO COMPLETO DE LA PÁGINA (úsalo para identificar la comunidad autónoma, el año, las unidades monetarias y el tema):
{texto_pagina[:800] if texto_pagina else "No disponible"}

DATOS DE LA TABLA (página {pagina} de {fuente}):
{texto_tabla}

Tu tarea es convertir los datos de la tabla en texto narrativo en español.

Reglas estrictas:
- Usa EXACTAMENTE la misma terminología que aparece en el texto de la página y en la tabla. Si el documento dice "empleos no financieros", usa esa expresión exacta, no "gasto total". Si dice "dotación presupuestaria", usa "dotación presupuestaria".
- Menciona siempre y explícitamente: el nombre completo de la comunidad autónoma o comunidades, el año presupuestario, y las unidades monetarias (miles de euros o millones de euros)
- Menciona todas las cifras y conceptos relevantes de la tabla
- Si la tabla compara varias comunidades autónomas, menciona todas con sus cifras
- No inventes datos que no estén en la tabla o en el texto de la página
- No uses formato de lista ni bullets, solo prosa continua
- Máximo 200 palabras

Escribe el texto narrativo:"""

    respuesta = client.chat.completions.create(
        model=MODELO_NARRATIVIZADOR,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500
    )
    return respuesta.choices[0].message.content.strip()


def narrativizar_chunks(chunks):
    chunks_narrativizados = []
    total_tablas = len([c for c in chunks if c["tipo"] == "tabla"])
    tablas_procesadas = 0

    print(f"   Narrativizando {total_tablas} tablas con GPT-4o...")

    for chunk in chunks:
        if chunk["tipo"] == "texto":
            chunks_narrativizados.append(chunk)
            continue

        try:
            texto_narrativo = narrativizar_tabla(
                chunk["texto"],
                chunk["pagina"],
                chunk["fuente"],
                chunk.get("texto_pagina", "")
            )
            chunks_narrativizados.append({
                "texto": texto_narrativo,
                "pagina": chunk["pagina"],
                "fuente": chunk["fuente"],
                "tipo": "tabla_narrativizada"
            })
            tablas_procesadas += 1
            print(f"   Tabla {tablas_procesadas}/{total_tablas} narrativizada (página {chunk['pagina']})")
            time.sleep(PAUSA_ENTRE_LLAMADAS)

        except Exception as e:
            print(f"   ERROR narrativizando tabla página {chunk['pagina']}: {e}")
            chunks_narrativizados.append(chunk)

    return chunks_narrativizados


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
        print(f"   Extrayendo texto y tablas...")
        paginas = extraer(ruta_pdf)
        datos_json.extend(paginas)
        guardar_json(datos_json)
        fuentes_procesadas.add(ruta_pdf)
        print(f"   {len(paginas)} páginas añadidas a datos_extraidos.json")

    print(f"   Generando chunks...")
    chunks = chunkear(paginas)
    print(f"   Chunks generados: {len(chunks)}")

    for chunk in chunks:
        if chunk["tipo"] == "texto":
            chunk["texto"] = normalizar_texto(chunk["texto"])

    print(f"   Narrativizando tablas...")
    chunks_narrativizados = narrativizar_chunks(chunks)
    print(f"   Chunks narrativizados: {len(chunks_narrativizados)}")

    print(f"   Vectorizando y subiendo a ChromaDB...")
    vectorizar(chunks_narrativizados, ruta_pdf)

    print(f"   Listo.")


def main():
    pdfs = [f for f in os.listdir("data/raw") if f.endswith(".pdf")]

    if not pdfs:
        print("No hay PDFs en data/raw/")
        return

    datos_json = cargar_json_existente()
    fuentes_procesadas = fuentes_en_json(datos_json)
    print(f"PDFs en datos_extraidos.json: {len(fuentes_procesadas)}")
    print(f"PDFs encontrados en data/raw: {len(pdfs)}")

    for pdf in pdfs:
        ruta = f"data/raw/{pdf}"
        procesar_pdf(ruta, datos_json, fuentes_procesadas)

    total = coleccion.count()
    print(f"\nPipeline completado.")
    print(f"Total páginas en datos_extraidos.json: {len(datos_json)}")
    print(f"Total vectores en base de datos: {total}")


main()
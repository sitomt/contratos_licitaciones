import json
import time
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODELO_NARRATIVIZADOR = "gpt-4o"
PAUSA_ENTRE_LLAMADAS = 0.5


def narrativizar_tabla(texto_tabla, pagina, fuente):
    prompt = f"""Eres un experto en presupuestos públicos españoles.
Tienes delante los datos de una tabla extraída de un documento presupuestario oficial.
Tu tarea es convertir esos datos en texto narrativo en español, claro y completo.

Reglas:
- Menciona explícitamente todas las cifras y conceptos de la tabla
- Usa lenguaje natural, como si explicaras el presupuesto a un ciudadano
- No inventes datos que no estén en la tabla
- No uses formato de lista ni bullets, solo prosa continua
- El texto debe ser rico en vocabulario para facilitar búsquedas semánticas

Datos de la tabla (página {pagina} de {fuente}):
{texto_tabla}

Escribe el texto narrativo:"""

    respuesta = cliente.chat.completions.create(
        model=MODELO_NARRATIVIZADOR,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )

    return respuesta.choices[0].message.content.strip()


def procesar_chunks():
    with open("data/processed/chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    chunks_narrativizados = []
    tablas_procesadas = 0
    errores = 0

    total_tablas = len([c for c in chunks if c["tipo"] == "tabla"])
    print(f"Total chunks: {len(chunks)}")
    print(f"Chunks de tabla a narrativizar: {total_tablas}")
    print(f"Chunks de texto (sin cambios): {len(chunks) - total_tablas}")
    print("-" * 50)

    for i, chunk in enumerate(chunks):
        if chunk["tipo"] == "texto":
            chunks_narrativizados.append(chunk)
            continue

        print(f"Narrativizando tabla {tablas_procesadas + 1}/{total_tablas} (página {chunk['pagina']})...")

        try:
            texto_narrativo = narrativizar_tabla(
                chunk["texto"],
                chunk["pagina"],
                chunk["fuente"]
            )
            chunk_nuevo = {
                "texto": texto_narrativo,
                "pagina": chunk["pagina"],
                "fuente": chunk["fuente"],
                "tipo": "tabla_narrativizada"
            }
            chunks_narrativizados.append(chunk_nuevo)
            tablas_procesadas += 1
            time.sleep(PAUSA_ENTRE_LLAMADAS)

        except Exception as e:
            print(f"  ERROR en página {chunk['pagina']}: {e}")
            chunks_narrativizados.append(chunk)
            errores += 1

    with open("data/processed/chunks_narrativizados.json", "w", encoding="utf-8") as f:
        json.dump(chunks_narrativizados, f, ensure_ascii=False, indent=2)

    print("-" * 50)
    print(f"Tablas narrativizadas: {tablas_procesadas}")
    print(f"Errores: {errores}")
    print(f"Total chunks guardados: {len(chunks_narrativizados)}")
    print(f"Guardado en: data/processed/chunks_narrativizados.json")


if __name__ == "__main__":
    procesar_chunks()
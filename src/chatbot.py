import os
from openai import OpenAI
from dotenv import load_dotenv
import chromadb

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma = chromadb.PersistentClient(path="data/vectordb")
coleccion = chroma.get_or_create_collection(name="presupuestos")

def buscar_chunks_relevantes(pregunta, n=6):
    respuesta = client.embeddings.create(
        input=pregunta,
        model="text-embedding-3-small"
    )
    vector_pregunta = respuesta.data[0].embedding

    resultados = coleccion.query(
        query_embeddings=[vector_pregunta],
        n_results=n
    )

    chunks = []
    for i in range(len(resultados["documents"][0])):
        chunks.append({
            "texto": resultados["documents"][0][i],
            "pagina": resultados["metadatas"][0][i]["pagina"],
            "fuente": resultados["metadatas"][0][i]["fuente"],
            "tipo": resultados["metadatas"][0][i]["tipo"]
        })

    return chunks

def responder(pregunta):
    chunks = buscar_chunks_relevantes(pregunta)

    contexto = ""
    for chunk in chunks:
        contexto += f"[Pagina {chunk['pagina']} | {chunk['fuente']}] {chunk['texto']}\n\n"

    prompt = f"""Eres un asistente de transparencia publica que ayuda a los ciudadanos a entender los presupuestos de las comunidades autonomas de España 2026.

Responde de forma clara y simple. Sigue estas reglas:
- Si tienes datos exactos en el contexto,usalos y cita la pagina
- Si tienes datos parciales de varias comunidades, comparalos aunque sean incompletos y dilo
- Si el contexto tiene datos de varias comunidades, presentalos todos ordenados
- Nunca inventes cifras
- Si no tienes suficiente informacion, explica que datos si tienes y sugiere una pregunta mas concreta que podria funcionar mejor

CONTEXTO DEL PRESUPUESTO:
{contexto}

PREGUNTA DEL CIUDADANO:
{pregunta}

RESPUESTA:"""

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return respuesta.choices[0].message.content

print("Chatbot de Presupuestos 2026 — Comunidades Autonomas de Espana")
print("Escribe 'salir' para terminar\n")

while True:
    pregunta = input("Tu pregunta: ")
    if pregunta.lower() == "salir":
        break
    if not pregunta.strip():
        continue

    print("\nBuscando respuesta...\n")
    respuesta = responder(pregunta)
    print(f"Respuesta: {respuesta}\n")
    print("-" * 50 + "\n")
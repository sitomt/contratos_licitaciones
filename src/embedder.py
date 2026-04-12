import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import chromadb

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_embedding(texto):
    respuesta = client.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    return respuesta.data[0].embedding

def procesar_embeddings():
    with open("data/processed/chunks_narrativizados.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    chroma = chromadb.PersistentClient(path="data/vectordb")
    coleccion = chroma.get_or_create_collection(name="presupuestos")

    print(f"Total chunks a vectorizar: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        texto = chunk["texto"]
        if not texto.strip():
            continue

        vector = generar_embedding(texto)

        coleccion.add(
            ids=[f"chunk_{i}"],
            embeddings=[vector],
            documents=[texto],
            metadatas=[{
                "pagina": chunk["pagina"],
                "fuente": chunk["fuente"],
                "tipo": chunk["tipo"]
            }]
        )

        print(f"chunk {i+1}/{len(chunks)} vectorizado")

    print(f"\nBase vectorial creada en data/vectordb")
    print(f"Total vectores almacenados: {coleccion.count()}")

procesar_embeddings()
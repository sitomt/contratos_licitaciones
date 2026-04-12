import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import chromadb

load_dotenv()

app = FastAPI(title="API Presupuestos RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma = chromadb.PersistentClient(path="data/vectordb")
coleccion = chroma.get_or_create_collection(name="presupuestos")


# ── Modelos de entrada ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    pregunta: str
    historial: List = []


# ── POST /chat ──────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(req: ChatRequest):
    if not req.pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")

    # Embed pregunta
    embed_resp = client.embeddings.create(
        input=req.pregunta,
        model="text-embedding-3-small"
    )
    vector_pregunta = embed_resp.data[0].embedding

    # Buscar top-6 chunks en ChromaDB
    resultados = coleccion.query(
        query_embeddings=[vector_pregunta],
        n_results=6,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    contexto = ""
    for i in range(len(resultados["documents"][0])):
        texto = resultados["documents"][0][i]
        meta = resultados["metadatas"][0][i]
        distancia = resultados["distances"][0][i]
        fuente = meta.get("fuente", "")
        pagina = meta.get("pagina", 0)

        chunks.append({
            "texto": texto,
            "fuente": fuente,
            "pagina": pagina,
            "distancia": distancia
        })
        contexto += f"[Pagina {pagina} | {fuente}] {texto}\n\n"

    # Llamar GPT-4o-mini
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
{req.pregunta}

RESPUESTA:"""

    gpt_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    respuesta = gpt_resp.choices[0].message.content

    return {"respuesta": respuesta, "chunks": chunks}


# ── GET /vectores ───────────────────────────────────────────────────────────

@app.get("/vectores")
def vectores():
    datos = coleccion.get(include=["embeddings", "documents", "metadatas"])

    embeddings = datos["embeddings"]
    documentos = datos["documents"]
    metadatas = datos["metadatas"]

    if embeddings is None or len(embeddings) == 0:
        return {"puntos": []}

    from sklearn.decomposition import PCA

    matriz = np.array(embeddings)
    reducer = PCA(n_components=3, random_state=42)
    coords = reducer.fit_transform(matriz)

    puntos = []
    for i in range(len(documentos)):
        meta = metadatas[i] if metadatas is not None and len(metadatas) > 0 else {}
        puntos.append({
            "x": float(coords[i][0]),
            "y": float(coords[i][1]),
            "z": float(coords[i][2]),
            "texto": documentos[i],
            "fuente": meta.get("fuente", ""),
            "pagina": meta.get("pagina", 0)
        })

    return {"puntos": puntos}


# ── GET /health ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    count = coleccion.count()
    return {"status": "ok", "vectores": count}

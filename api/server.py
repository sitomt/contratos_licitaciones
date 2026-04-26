import os
import sqlite3
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
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

NOMBRES_DOCUMENTOS = {
    "presupuestos_generales_2026.pdf": "Presupuestos Generales Madrid 2026",
    "resumen_ingresos_y_gastos.pdf": "Resumen Ingresos y Gastos Madrid",
    "andalucia.pdf": "Presupuestos Comunidad de Andalucía 2026",
    "castillalamancha.pdf": "Presupuestos Castilla-La Mancha 2026",
    "castillayleon.pdf": "Presupuestos Castilla y León 2026",
}

DB_PATH = "data/logs/conversaciones.db"


def init_db():
    os.makedirs("data/logs", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            pregunta TEXT NOT NULL,
            hipotesis_hyde TEXT,
            respuesta TEXT NOT NULL,
            score_medio REAL,
            num_chunks INTEGER,
            fuentes TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


# ── Modelos de entrada ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    pregunta: str
    historial: List = []
    sesion_id: Optional[str] = None


# ── POST /chat ──────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(req: ChatRequest):
    if not req.pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")

    embed_resp = client.embeddings.create(
        input=req.pregunta,
        model="text-embedding-3-small"
    )
    vector_pregunta = embed_resp.data[0].embedding

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
- Si tienes datos exactos en el contexto, usalos y cita la pagina
- Si la pregunta pide comparar varias comunidades, lista TODAS las que aparezcan en el contexto con sus cifras concretas, ordenadas de mayor a menor
- Si el contexto no cubre todas las comunidades de España, indica explicitamente cuales tienes y cuales no, en lugar de decir simplemente que no tienes datos
- Nunca inventes cifras
- Si no tienes suficiente informacion sobre alguna comunidad concreta, sugiere preguntar especificamente por ella

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

    # Deduplicar fuentes por documento con nombre legible
    fuentes_dict = {}
    for chunk in chunks:
        basename = os.path.basename(chunk["fuente"])
        doc = NOMBRES_DOCUMENTOS.get(basename, os.path.splitext(basename)[0])
        pag = chunk["pagina"]
        if doc not in fuentes_dict:
            fuentes_dict[doc] = set()
        fuentes_dict[doc].add(pag)
    fuentes_log = [{"documento": d, "paginas": sorted(list(p))} for d, p in fuentes_dict.items()]

    # Logging en SQLite
    avg_dist = sum(c["distancia"] for c in chunks) / len(chunks) if chunks else None
    score_medio = round((2 - avg_dist) / 2 * 100, 2) if avg_dist is not None else None
    sid = req.sesion_id or str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO conversaciones (sesion_id, timestamp, pregunta, hipotesis_hyde, respuesta, score_medio, num_chunks, fuentes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (sid, datetime.utcnow().isoformat(), req.pregunta, None, respuesta, score_medio, len(chunks), json.dumps(fuentes_log, ensure_ascii=False))
    )
    conn.commit()
    conn.close()

    return {
        "respuesta": respuesta,
        "chunks": chunks,
        "fuentes": fuentes_log if fuentes_log else [],
        "score_similitud_media": score_medio
    }


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
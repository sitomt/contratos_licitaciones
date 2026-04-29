import os
import sqlite3
import json
import uuid
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
    "castillayleon.pdf": "Presupuestos Castilla y León 2026",
    "valencia.pdf": "Presupuestos Comunidad Valenciana 2026",
}



DB_PATH = "data/logs/conversaciones.db"

TEMAS_KEYWORDS = {
    "Sanidad": ["sanidad","salud","hospital","médico","sanitario"],
    "Educación": ["educación","escuela","universidad","colegio","enseñanza"],
    "Infraestructuras": ["infraestructura","carretera","transporte","obra","tren"],
    "Pensiones": ["pensión","jubilación","pensionista","seguridad social"],
    "Empleo": ["empleo","trabajo","paro","desempleo","laboral"],
    "Vivienda": ["vivienda","alquiler","hipoteca","casa"],
    "Cultura": ["cultura","museo","arte","patrimonio"],
    "Medioambiente": ["medioambiente","ecología","sostenible","clima","verde"],
    "Tecnología": ["tecnología","digital","innovación","inteligencia artificial"],
    "Impuestos": ["impuesto","tributo","fiscal","irpf","iva","tasas"],
}

COMUNIDADES_FUENTES = {
    "andalucia": ["andalucia.pdf"],
    "madrid": ["presupuestos_generales_2026.pdf", "resumen_ingresos_y_gastos.pdf"],
    "castillayleon": ["castillayleon.pdf"],
}

KEYWORDS_COMUNIDADES = {
    "andalucia": ["andalucía", "andalucia", "sevilla", "málaga", "granada"],
    "madrid": ["madrid", "comunidad de madrid"],
    "castillayleon": ["castilla y león", "castilla y leon", "castillayleon",
                      "valladolid", "burgos", "salamanca", "león"],
}

KEYWORDS_COMPARATIVA = [
    "compara", "comparar", "diferencia", "más que", "menos que",
    "mayor que", "menor que", "versus", "vs", "todas",
    "cada comunidad", "qué comunidad", "cuál comunidad",
]


def detectar_tema(pregunta: str) -> str:
    p = pregunta.lower()
    for tema, kws in TEMAS_KEYWORDS.items():
        if any(k in p for k in kws):
            return tema
    return "General"


def detectar_comunidades(pregunta: str) -> list:
    p = pregunta.lower()
    detectadas = []
    for clave, keywords in KEYWORDS_COMUNIDADES.items():
        if any(kw in p for kw in keywords):
            if clave not in detectadas:
                detectadas.append(clave)
    return detectadas


def es_comparativa(pregunta: str) -> bool:
    p = pregunta.lower()
    return any(kw in p for kw in KEYWORDS_COMPARATIVA)


def _procesar_resultados(resultados: dict) -> list:
    chunks = []
    docs = resultados["documents"][0] if resultados["documents"] else []
    metas = resultados["metadatas"][0] if resultados["metadatas"] else []
    dists = resultados["distances"][0] if resultados["distances"] else []
    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        chunks.append({
            "texto": doc,
            "fuente": meta.get("fuente", ""),
            "pagina": meta.get("pagina", 0),
            "distancia": dists[i],
        })
    return chunks


def busqueda_balanceada(vector_pregunta: list, comunidades: list, comparativa: bool) -> tuple:
    MAX_CHUNKS_TOTAL = 12  # techo de seguridad para el contexto del LLM

    def query_global():
        r = coleccion.query(
            query_embeddings=[vector_pregunta], n_results=6,
            include=["documents", "metadatas", "distances"]
        )
        return _procesar_resultados(r)

    if not comunidades and not comparativa:
        return query_global(), "global"

    if len(comunidades) == 1 and not comparativa:
        fuentes = COMUNIDADES_FUENTES.get(comunidades[0], [])
        where_filter = {"fuente": {"$in": [f"data/raw/{f}" for f in fuentes]}}
        try:
            resultados = coleccion.query(
                query_embeddings=[vector_pregunta], n_results=6,
                where=where_filter, include=["documents", "metadatas", "distances"]
            )
            chunks = _procesar_resultados(resultados)
            if chunks:
                return chunks, f"filtrado_{comunidades[0]}"
        except Exception as e:
            print(f"[busqueda_balanceada] filtro fallido para '{comunidades[0]}': {e}")
        return query_global(), "global_fallback"

    if comunidades:
        comunidades_a_consultar = comunidades
        n_por_comunidad = max(2, 6 // len(comunidades))
    else:
        comunidades_a_consultar = list(COMUNIDADES_FUENTES.keys())
        n_por_comunidad = 2

    chunks_por_comunidad = []
    for comunidad in comunidades_a_consultar:
        fuentes = COMUNIDADES_FUENTES.get(comunidad, [])
        if not fuentes:
            continue
        where_filter = {"fuente": {"$in": [f"data/raw/{f}" for f in fuentes]}}
        try:
            resultados = coleccion.query(
                query_embeddings=[vector_pregunta], n_results=n_por_comunidad,
                where=where_filter, include=["documents", "metadatas", "distances"]
            )
            chunks_por_comunidad.extend(_procesar_resultados(resultados))
        except Exception as e:
            print(f"[busqueda_balanceada] filtro fallido para '{comunidad}': {e}")
            continue

    if not chunks_por_comunidad:
        return query_global(), "global_fallback"

    chunks_por_comunidad.sort(key=lambda x: x["distancia"])
    return chunks_por_comunidad[:MAX_CHUNKS_TOTAL], f"balanceado_{len(comunidades_a_consultar)}comunidades"


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
    for col, tipo in [
        ("latencia_ms","INTEGER"), ("tokens_prompt","INTEGER"),
        ("tokens_respuesta","INTEGER"), ("coste_estimado_eur","REAL"),
        ("evaluacion_agente","TEXT"), ("score_evaluacion","REAL"),
        ("tema_detectado","TEXT"), ("pregunta_respondida","INTEGER"),
        ("longitud_respuesta","INTEGER"), ("session_turno","INTEGER"),
        ("feedback_tipo","TEXT"), ("feedback_comentario","TEXT"),
        ("estrategia_busqueda","TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE conversaciones ADD COLUMN {col} {tipo}")
        except Exception:
            pass
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")


# ── Modelos de entrada ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    pregunta: str
    historial: List = []
    sesion_id: Optional[str] = None


# ── POST /chat ──────────────────────────────────────────────────────────────

@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")

    t0 = time.time()

    embed_resp = client.embeddings.create(
        input=req.pregunta, model="text-embedding-3-small"
    )
    vector_pregunta = embed_resp.data[0].embedding

    comunidades = detectar_comunidades(req.pregunta)
    comparativa = es_comparativa(req.pregunta)
    chunks, estrategia = busqueda_balanceada(vector_pregunta, comunidades, comparativa)

    contexto = ""
    for chunk in chunks:
        contexto += f"[Pagina {chunk['pagina']} | {chunk['fuente']}] {chunk['texto']}\n\n"

    prompt = f"""Eres un asistente de transparencia publica que ayuda a los ciudadanos a entender los presupuestos de las comunidades autonomas de España 2026.

Responde de forma clara y simple. Sigue estas reglas:
- Si tienes datos exactos en el contexto, usalos y cita la pagina
- Si la pregunta pide comparar varias comunidades, lista TODAS las que aparezcan en el contexto
- Nunca inventes cifras
- Si no tienes suficiente informacion, indícalo claramente

CONTEXTO DEL PRESUPUESTO:
{contexto}

PREGUNTA DEL CIUDADANO:
{req.pregunta}

RESPUESTA:"""

    gpt_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3
    )
    respuesta = gpt_resp.choices[0].message.content
    latencia_ms = int((time.time() - t0) * 1000)

    fuentes_dict = {}
    for chunk in chunks:
        basename = os.path.basename(chunk["fuente"])
        doc = NOMBRES_DOCUMENTOS.get(basename, os.path.splitext(basename)[0])
        pag = chunk["pagina"]
        if doc not in fuentes_dict:
            fuentes_dict[doc] = set()
        fuentes_dict[doc].add(pag)
    fuentes_log = [{"documento":d,"paginas":sorted(list(p))} for d,p in fuentes_dict.items()]

    avg_dist = sum(c["distancia"] for c in chunks)/len(chunks) if chunks else None
    score_medio = round((2-avg_dist)/2*100,2) if avg_dist is not None else None

    tokens_p = gpt_resp.usage.prompt_tokens
    tokens_r = gpt_resp.usage.completion_tokens
    coste_eur = round((tokens_p*0.00000015 + tokens_r*0.0000006)*0.92, 6)
    tema = detectar_tema(req.pregunta)
    evaluacion = "coherente" if (score_medio or 0)>=80 else "parcial" if (score_medio or 0)>=60 else "incoherente"
    pregunta_respondida = 1 if (score_medio or 0)>=70 else 0
    longitud = len(respuesta)
    sid = req.sesion_id or str(uuid.uuid4())

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM conversaciones WHERE sesion_id=?", (sid,))
    session_turno = (cur.fetchone()[0] or 0) + 1
    cur.execute("""
        INSERT INTO conversaciones (
            sesion_id,timestamp,pregunta,hipotesis_hyde,respuesta,
            score_medio,num_chunks,fuentes,
            latencia_ms,tokens_prompt,tokens_respuesta,coste_estimado_eur,
            evaluacion_agente,score_evaluacion,tema_detectado,
            pregunta_respondida,longitud_respuesta,session_turno,
            estrategia_busqueda
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        sid, datetime.utcnow().isoformat(), req.pregunta, None, respuesta,
        score_medio, len(chunks), json.dumps(fuentes_log, ensure_ascii=False),
        latencia_ms, tokens_p, tokens_r, coste_eur,
        evaluacion, score_medio, tema,
        pregunta_respondida, longitud, session_turno,
        estrategia
    ))
    conv_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": conv_id,
        "sesion_id": sid,
        "respuesta": respuesta,
        "chunks": chunks,
        "fuentes": fuentes_log if fuentes_log else [],
        "score_similitud_media": score_medio,
        "latencia_ms": latencia_ms,
        "estrategia_busqueda": estrategia,
    }


# ── GET /vectores ───────────────────────────────────────────────────────────

@app.get("/api/vectores")
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

@app.get("/api/health")
def health():
    count = coleccion.count()
    return {"status": "ok", "vectores": count}


# ── PATCH /feedback/{id} ────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    tipo: str
    comentario: Optional[str] = None

@app.patch("/api/feedback/{conv_id}")
def feedback(conv_id: int, req: FeedbackRequest):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE conversaciones SET feedback_tipo=?, feedback_comentario=? WHERE id=?",
        (req.tipo, req.comentario, conv_id)
    )
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="No encontrado")
    conn.commit()
    conn.close()
    return {"ok": True}


# ── GET /metrics ─────────────────────────────────────────────────────────────

@app.get("/api/metrics")
def metrics():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM conversaciones")
    total = cur.fetchone()[0]

    cur.execute("SELECT AVG(score_medio) FROM conversaciones WHERE score_medio IS NOT NULL")
    score_avg = round(cur.fetchone()[0] or 0, 1)

    cur.execute("SELECT AVG(latencia_ms) FROM conversaciones WHERE latencia_ms IS NOT NULL")
    lat = cur.fetchone()[0]
    latencia_avg = round(lat) if lat else 0

    cur.execute("SELECT SUM(coste_estimado_eur) FROM conversaciones WHERE coste_estimado_eur IS NOT NULL")
    coste = cur.fetchone()[0]
    coste_total = round(coste or 0, 4)

    cur.execute("SELECT COUNT(*) FROM conversaciones WHERE pregunta_respondida=0")
    sin_respuesta = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM conversaciones WHERE evaluacion_agente='coherente'")
    coherentes = cur.fetchone()[0]
    pct_coherentes = round(coherentes/total*100, 1) if total > 0 else 0

    cur.execute("""
        SELECT tema_detectado, COUNT(*) as cnt FROM conversaciones
        WHERE tema_detectado IS NOT NULL
        GROUP BY tema_detectado ORDER BY cnt DESC LIMIT 8
    """)
    temas = [{"tema": r[0], "count": r[1]} for r in cur.fetchall()]

    cur.execute("""
        SELECT id, timestamp, pregunta, score_medio, evaluacion_agente,
               feedback_tipo, tema_detectado, latencia_ms
        FROM conversaciones ORDER BY id DESC LIMIT 20
    """)
    cols = ["id","timestamp","pregunta","score_medio","evaluacion_agente",
            "feedback_tipo","tema_detectado","latencia_ms"]
    logs = [dict(zip(cols, row)) for row in cur.fetchall()]

    cur.execute("""
        SELECT COUNT(*) FROM conversaciones
        WHERE timestamp > datetime('now','-1 day') AND score_medio < 60
    """)
    alertas_baja = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM conversaciones
        WHERE feedback_tipo='negativo'
        AND timestamp > datetime('now','-7 day')
    """)
    feedbacks_negativos = cur.fetchone()[0]

    cur.execute("""
        SELECT estrategia_busqueda, COUNT(*) as cnt FROM conversaciones
        WHERE estrategia_busqueda IS NOT NULL
        GROUP BY estrategia_busqueda ORDER BY cnt DESC
    """)
    estrategias = [{"estrategia": r[0], "count": r[1]} for r in cur.fetchall()]

    conn.close()
    return {
        "total_consultas": total,
        "score_medio_global": score_avg,
        "latencia_media_ms": latencia_avg,
        "coste_total_eur": coste_total,
        "sin_respuesta_suficiente": sin_respuesta,
        "pct_coherentes": pct_coherentes,
        "temas_top": temas,
        "logs_recientes": logs,
        "estrategias_busqueda": estrategias,
        "alertas": {
            "baja_similitud_24h": alertas_baja,
            "feedbacks_negativos_7d": feedbacks_negativos,
        }
    }


# ── GET /documentos ──────────────────────────────────────────────────────────

@app.get("/api/documentos")
def documentos():
    todos = coleccion.get(include=["metadatas"])
    chunks_por_doc = {}
    for meta in (todos["metadatas"] or []):
        fname = os.path.basename(meta.get("fuente",""))
        chunks_por_doc[fname] = chunks_por_doc.get(fname, 0) + 1

    docs = []
    raw_dir = "data/raw"
    if os.path.exists(raw_dir):
        for filename in sorted(os.listdir(raw_dir)):
            if not filename.endswith(".pdf"):
                continue
            filepath = os.path.join(raw_dir, filename)
            size_mb = round(os.path.getsize(filepath)/(1024*1024), 1)
            nombre = NOMBRES_DOCUMENTOS.get(filename, os.path.splitext(filename)[0])
            chunks = chunks_por_doc.get(filename, 0)
            docs.append({
                "filename": filename,
                "nombre": nombre,
                "size_mb": size_mb,
                "chunks": chunks,
                "indexado": chunks > 0,
            })
    return {"documentos": docs}


# ── POST /upload ─────────────────────────────────────────────────────────────

from fastapi import UploadFile, File
import shutil

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan PDFs")
    dest = os.path.join("data/raw", file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"ok": True, "filename": file.filename}

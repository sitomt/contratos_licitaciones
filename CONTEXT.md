# PROYECTO: Plataforma de Transparencia Ciudadana
## Contexto para asistente IA — Master IA ISDI 2026

---

## IDENTIDAD DEL PROYECTO

Sistema RAG de transparencia pública con dos bloques:
- **Bloque A** (COMPLETADO): Chatbot que responde preguntas sobre presupuestos públicos en lenguaje natural
- **Bloque B** (EN CURSO): Detección de anomalías en licitaciones públicas españolas



---

## BLOQUE A — ARQUITECTURA RAG COMPLETA

### Stack tecnológico
- **Extracción PDF**: pdfplumber (texto + tablas)
- **Embeddings**: OpenAI text-embedding-3-small (vectores 1536d)
- **Vector store**: ChromaDB local (data/vectordb/) — sqlite3
- **LLM**: GPT-4o-mini, temperature=0.3
- **Entorno**: Python 3.14.3, venv, macOS, VSCode

### Pipeline offline (pipeline.py orquesta todo)
```
data/raw/*.pdf
  → src/extractor.py     → data/processed/datos_extraidos.json
  → src/chunker.py       → data/processed/chunks.json
  → src/embedder.py      → data/vectordb/ (ChromaDB)
```

### Pipeline online (src/chatbot.py)
```
pregunta usuario
  → embed pregunta (OpenAI text-embedding-3-small)
  → ChromaDB query (top-6 chunks, similitud coseno)
  → prompt = contexto_chunks + pregunta
  → GPT-4o-mini → respuesta con cita de página
```

### Parámetros clave
- Chunk size: 500 tokens
- Solapamiento: 50 tokens
- Tablas: 1 chunk por tabla completa (cabecera+filas como "col: valor | col: valor")
- Chunks recuperados en query: n=6
- Total vectores actuales: 543

### Documentos indexados
- presupuestos_generales_2026.pdf — Comunidad de Madrid 2026 (50 págs)
- resumen_ingresos_y_gastos.pdf — Resumen ingresos/gastos Madrid (3 págs)
- ResumenEjecutivo2026.pdf — Presupuestos todas las CC.AA. España 2026 (241 págs)

### Procesamiento incremental
pipeline.py detecta si un PDF ya está en ChromaDB por fuente. Si existe → salta. Si no → procesa y añade. No duplica vectores.

---

## ESTRUCTURA DE CARPETAS

```
Isdi-presupuestos_estado/
├── data/
│   ├── raw/              ← PDFs fuente (nunca modificar)
│   ├── processed/        ← JSONs intermedios (regenerables)
│   └── vectordb/         ← ChromaDB (regenerable con pipeline.py)
├── src/
│   ├── extractor.py      ← pdfplumber → JSON
│   ├── chunker.py        ← JSON → chunks con solapamiento
│   ├── embedder.py       ← chunks → vectores ChromaDB
│   ├── chatbot.py        ← interfaz conversacional terminal
│   ├── procesador_tablas.py ← script debug inspección tablas
│   └── descargador_licitaciones.py ← prototipo Bloque B
├── pipeline.py           ← orquestador Bloque A
├── .env                  ← OPENAI_API_KEY (nunca a Git)
├── .gitignore            ← venv/, __pycache__/, .env
└── requirements.txt      ← todas las dependencias con versiones
```

---

## COMANDOS CLAVE

```bash
# Ejecutar chatbot
venv/bin/python src/chatbot.py

# Reindexar (añadir PDFs nuevos a data/raw/ primero)
venv/bin/python pipeline.py

# Reconstruir entorno si venv se rompe
rm -rf venv && python3 -m venv venv && venv/bin/pip install -r requirements.txt
```

**IMPORTANTE**: Usar siempre `venv/bin/python` y `venv/bin/pip` — Claude Code rompe el PATH del terminal en macOS y `python`/`python3` apuntan al Homebrew global sin las librerías del proyecto.

---

## LIMITACIONES CONOCIDAS

### Limitación crítica — tablas
Las tablas se vectorizan como texto con formato "cabecera: valor | cabecera: valor". Funciona para preguntas directas pero falla en:
- Rankings entre todas las CC.AA. ("cuál tiene mayor presupuesto")
- Comparativas que cruzan múltiples secciones del documento
- Causa: mismatch de vocabulario entre términos técnicos del PDF ("empleos no financieros") y lenguaje natural ("presupuesto total")

**Solución diseñada (Camino B, no implementada)**: llamar API Claude para convertir cada tabla en texto narrativo ANTES de vectorizar. Esto normaliza el vocabulario y resuelve el problema.

### Limitación — páginas escaneadas
Páginas 48-50 del PDF principal son imágenes. pdfplumber no extrae texto. Necesitaría OCR (pytesseract) — no implementado.

### Funciona bien
- Preguntas directas con dato concreto ("cuánto a Sanidad")
- Comparativas entre 2 comunidades específicas
- Preguntas de contexto narrativo
- Cita automática de página fuente en cada respuesta

---

## BLOQUE B — ESTADO Y PLAN

### Objetivo
Detectar contratos públicos españoles con patrones de fraude usando ML no supervisado.

### Pipeline planificada (equipo de 4 personas)
1. Ingesta de datos — descarga contratos de PLACE/datos.gob.es
2. **Procesamiento y normalización** ← PARTE DE GINES
3. Feature Engineering + ML (Isolation Forest)
4. Visualización / Dashboard de alertas

### Estado actual
- PLACE API requiere certificado digital → descartada para prototipo
- Alternativa viable: datos.gob.es — datasets CSV de contratos Ministerio de Hacienda, descarga directa sin auth
- src/descargador_licitaciones.py es exploración inicial, no integrado en pipeline
- Ningún script de Bloque B está operativo todavía

### Features de fraude planificadas
- ratio_concentracion: % contratos del organismo que gana esta empresa
- cerca_umbral: importe entre 45.000-50.000€ (fraccionamiento)
- baja_concurrencia: menos de 2 licitadores
- modificado_significativo: modificación > 20% precio original
- dias_adjudicacion_ratio: velocidad adjudicación vs media

### Algoritmo central
Isolation Forest (sklearn.ensemble) — no supervisado, no requiere datos etiquetados, detecta anomalías estadísticas en espacio n-dimensional de features.

---

## DECISIONES DE DISEÑO

| Decisión | Elección | Razón |
|----------|----------|-------|
| Vector store | ChromaDB local | Sin cuenta externa, gratuito, suficiente para PoC |
| Embedding model | text-embedding-3-small | Coste/calidad óptimo para español |
| LLM | GPT-4o-mini | 95% calidad GPT-4o a fracción del coste |
| Temperature | 0.3 | Conservador — evita inventar cifras en sistema de transparencia |
| Chunk size | 500 tokens | Equilibrio contexto/precisión del vector |
| Solapamiento | 50 tokens (10%) | Evita partir frases clave entre chunks |

---

## PRÓXIMOS PASOS IDENTIFICADOS

1. Descargar dataset CSV de contratos de datos.gob.es
2. Construir src/limpiador.py (procesamiento Bloque B — parte Gines)
3. Implementar Camino B para tablas (API Claude normaliza antes de vectorizar)
4. Interfaz web con Streamlit (pasar chatbot de terminal a web)
5. Despliegue en VPS (Hetzner ~4€/mes) para funcionamiento 24/7



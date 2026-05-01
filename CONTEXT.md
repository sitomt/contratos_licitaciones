# PROYECTO: Civitas — Transparencia Presupuestaria
## Contexto para asistente IA — Master IA ISDI 2026

---

## IDENTIDAD DEL PROYECTO

**Civitas** es un sistema RAG de transparencia pública con dos bloques:
- **Bloque A** (COMPLETO y FUNCIONAL con interfaz web): Chatbot que responde preguntas sobre presupuestos públicos en lenguaje natural
- **Bloque B** (ASPIRACIONAL — fuera del sprint actual): Detección de anomalías en licitaciones públicas españolas

---

## STACK TECNOLÓGICO ACTUAL

| Capa | Tecnología | Versión/Notas |
|------|-----------|---------------|
| Python | 3.11 | venv creado con `/opt/homebrew/bin/python3.11` |
| PDF extraction | pdfplumber | — |
| Embeddings | OpenAI text-embedding-3-small | vectores 1536d |
| Vector store | ChromaDB local | `data/vectordb/` (sqlite3) |
| LLM chatbot | GPT-4o-mini | temperature=0.3, cada query |
| LLM narrativizador | GPT-4o | ejecución única al procesar PDFs — convierte tablas a prosa |
| Reducción dim. | PCA (sklearn) | reemplazó a UMAP — ver decisiones técnicas |
| Backend | FastAPI 0.115.12 + Uvicorn | puerto 8000 |
| Frontend | Standalone HTML (`frontend/index.html`) — React 18 CDN + Babel standalone | sin build step en dev; `npm run build` para producción |
| Animación de entrada | Globe.gl 2.30.0 | Three.js — globo 3D interactivo de la pantalla Civitas |
| Visualización | plotly.js 2.32.0 | importado directo — ver decisiones técnicas |
| OS / entorno | macOS, VSCode | — |

> **IMPORTANTE sobre Python**: usar siempre `venv/bin/python` y `venv/bin/pip`.
> Claude Code y terminales macOS pueden apuntar al Python global de Homebrew sin las librerías del proyecto.

---

## BLOQUE A — ARQUITECTURA RAG COMPLETA

### Pipeline offline (`pipeline.py` orquesta todo internamente)
```
data/raw/*.pdf
  → pipeline.py (extracción con pdfplumber)
  → pipeline.py (chunking 500 tokens, solapamiento 50)
  → pipeline.py (narrativización de tablas con GPT-4o)   ← src/normalizador.py aplicado a chunks de texto
  → data/vectordb/ (ChromaDB)
```
> `pipeline.py` contiene toda la lógica internamente. El único módulo de `src/` que importa es `src/normalizador.py`.

### Pipeline online (`api/server.py` HTTP)
```
pregunta usuario
  → embed pregunta directamente (OpenAI text-embedding-3-small)
  → detectar_comunidades() + es_comparativa()
  → busqueda_balanceada(): ChromaDB query(s) con estrategia adaptada
      • 0 comunidades, no comparativa → top-6 global
      • 1 comunidad → top-6 filtrado por esa comunidad (where fuente)
      • 2+ comunidades o comparativa → top-N por comunidad, balanceado
  → prompt = contexto_chunks + pregunta
  → GPT-4o-mini → respuesta con cita de página
```

### Parámetros clave
- Chunk size: 500 tokens
- Solapamiento: 50 tokens (10%)
- Tablas: 1 chunk por tabla, narrativizado a prosa con GPT-4o antes de vectorizar
- Chunks recuperados en query: **n=6**
- Total vectores actuales: **1621** (BD reconstruida con los nuevos PDFs)

### Documentos indexados
| Fichero | Descripción | Chunks |
|---------|-------------|--------|
| `andalucia.pdf` | Presupuestos Comunidad de Andalucía 2026 | 890 |
| `castillayleon.pdf` | Presupuestos Castilla y León 2026 | 638 |
| `presupuestos_generales_2026.pdf` | Presupuestos Generales Madrid 2026 | 87 |
| `resumen_ingresos_y_gastos.pdf` | Resumen Ingresos y Gastos Madrid | 6 |

> Total: **1621 vectores** en ChromaDB. Los PDFs son documentos narrativos publicados directamente por las comunidades autónomas. Su vocabulario ya es cercano al lenguaje natural, lo que simplificó el pipeline (eliminación de HyDE).

### Procesamiento incremental
`pipeline.py` detecta si un PDF ya está en ChromaDB por la clave `fuente`. Si existe → salta. Si no → procesa y añade. No duplica vectores.

---

## ESTRUCTURA DE CARPETAS

```
Isdi-presupuestos/
├── api/
│   ├── __init__.py
│   └── server.py              ← FastAPI — endpoints con prefijo /api/ (ver sección API REST)
├── data/
│   ├── raw/                   ← PDFs fuente (NUNCA modificar)
│   ├── processed/             ← JSONs intermedios (regenerables con pipeline.py)
│   └── vectordb/              ← ChromaDB (regenerable con pipeline.py)
├── frontend/
│   ├── index.html             ← TODO el frontend activo: standalone HTML, React 18 CDN + Babel
│   ├── package.json
│   ├── vite.config.js         ← dev server puerto 5173, proxy /api/ → localhost:8000
│   └── src/                   ← legacy — frontend modular Vite original (no usado; superado por index.html)
│       ├── App.jsx
│       ├── main.jsx
│       └── components/        ← ChatPanel.jsx, TechPanel.jsx, VectorMap.jsx (no activos)
├── src/
│   ├── normalizador.py        ← ÚNICO MÓDULO ACTIVO: limpieza de texto plano pre-chunking
│   └── legacy/                ← lógica histórica absorbida por pipeline.py (referencia, no usados)
│       ├── chatbot.py         ← interfaz conversacional terminal
│       ├── chunker.py
│       ├── extractor.py
│       ├── narrativizador.py
│       └── embedder.py
├── pipeline.py                ← orquestador Bloque A (todo el procesamiento aquí)
├── start_api.sh               ← `source venv/bin/activate && uvicorn api.server:app --reload --port 8000`
├── requirements.txt           ← dependencias con versiones exactas
├── .env                       ← OPENAI_API_KEY (NUNCA a Git)
└── .gitignore                 ← venv/, __pycache__/, .env
```

> **Nota sobre src/**: Solo `normalizador.py` está activo. Los módulos históricos están en `src/legacy/` — su lógica fue absorbida por `pipeline.py`. Se mantienen como referencia pero no forman parte del flujo.
> **Nota sobre frontend/src/**: Código del frontend modular original (Vite + React separado). Completamente superado por `frontend/index.html`. No está activo ni desplegado.

---

## API REST (Bloque A — backend)

### Stack
- Framework: FastAPI 0.115
- Servidor: Uvicorn (ASGI), puerto 8000
- CORS: `allow_origins=["*"]` (acepta frontend local y producción)
- Arranque: `bash start_api.sh`

### Endpoints

> Todos los endpoints usan el prefijo `/api/`. El endpoint raíz `GET /` sirve `frontend/index.html`.

#### POST /api/chat
Responde preguntas sobre presupuestos usando el pipeline RAG completo.

**Request**
```json
{ "pregunta": "¿Cuánto destina Madrid a Sanidad?", "historial": [], "sesion_id": "uuid-opcional" }
```
**Response**
```json
{
  "id": 42,
  "sesion_id": "uuid-de-sesion",
  "respuesta": "Texto generado por GPT-4o-mini...",
  "chunks": [{ "texto": "...", "fuente": "...", "pagina": 12, "distancia": 0.23 }],
  "fuentes": [{ "documento": "Presupuestos Generales Madrid 2026", "paginas": [12, 15] }],
  "score_similitud_media": 87.4,
  "latencia_ms": 1240,
  "estrategia_busqueda": "filtrado_andalucia"
}
```
Valores posibles de `estrategia_busqueda`: `"global"` · `"filtrado_<comunidad>"` · `"balanceado_<N>comunidades"` · `"global_fallback"`

**Lógica**: embed pregunta directamente → detección de comunidades y comparativa → `busqueda_balanceada()` → prompt + GPT-4o-mini (temperature=0.3)

La recuperación es balanceada por comunidad cuando se detectan varias CCAA en la pregunta (ver Decisiones técnicas).

#### GET /api/vectores
Devuelve todos los vectores de ChromaDB reducidos a 3D con **PCA** (ya no UMAP).

**Response**
```json
{ "puntos": [{ "x": 1.23, "y": -0.45, "z": 2.11, "texto": "...", "fuente": "...", "pagina": 5 }] }
```

#### GET /api/health
```json
{ "status": "ok", "vectores": 1621 }
```

#### PATCH /api/feedback/{id}
Registra feedback del usuario sobre una respuesta.
```json
{ "tipo": "positivo", "comentario": "opcional" }
```

#### GET /api/metrics
Estadísticas globales: total consultas, score medio, latencia, coste, temas top, logs recientes, alertas.

#### GET /api/documentos
Lista los PDFs en `data/raw/` con su número de chunks indexados.

#### POST /api/upload
Sube un PDF a `data/raw/`. Requiere `python-multipart`.

---

## BASE DE DATOS SQLITE (`data/logs/conversaciones.db`)

Tabla `conversaciones` — 22 columnas totales. La migración es **defensiva**: `init_db()` añade las columnas nuevas con `ALTER TABLE` envuelto en `try/except`, por lo que no rompe una BD existente.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER PK | autoincremento |
| `sesion_id` | TEXT | UUID anónimo de sesión |
| `timestamp` | DATETIME | UTC ISO |
| `pregunta` | TEXT | pregunta del usuario |
| `hipotesis_hyde` | TEXT | siempre NULL (conservado por compatibilidad con logs anteriores) |
| `respuesta` | TEXT | respuesta generada |
| `score_medio` | REAL | similitud media en porcentaje (0-100) |
| `num_chunks` | INTEGER | chunks recuperados |
| `fuentes` | TEXT | JSON de fuentes citadas |
| `latencia_ms` | INTEGER | tiempo total de la request en ms |
| `tokens_prompt` | INTEGER | tokens enviados a GPT |
| `tokens_respuesta` | INTEGER | tokens generados por GPT |
| `coste_estimado_eur` | REAL | coste estimado en euros |
| `evaluacion_agente` | TEXT | "coherente" / "parcial" / "incoherente" |
| `score_evaluacion` | REAL | igual que score_medio (alias) |
| `tema_detectado` | TEXT | tema inferido por keywords |
| `pregunta_respondida` | INTEGER | 1 si score≥70, 0 si no |
| `longitud_respuesta` | INTEGER | caracteres de la respuesta |
| `session_turno` | INTEGER | número de turno dentro de la sesión |
| `feedback_tipo` | TEXT | "positivo" / "negativo" (actualizado por PATCH /api/feedback) |
| `feedback_comentario` | TEXT | comentario opcional del usuario |
| `estrategia_busqueda` | TEXT | estrategia RAG usada: `"global"` / `"filtrado_<comunidad>"` / `"balanceado_<N>comunidades"` / `"global_fallback"` |

---

## FRONTEND — Interfaz Web

### Stack
- **Un único archivo**: `frontend/index.html` — sin componentes separados, sin build en desarrollo
- React 18 via CDN (`unpkg.com/react@18.3.1`) + Babel standalone (`@babel/standalone@7.29.0`)
- Plotly.js via CDN (`cdn.plot.ly/plotly-2.32.0.min.js`)
- Estética "Liquid Glass": glassmorphism, fondo crema `#F8F7F4`, tipografías Playfair Display + DM Sans, acentos ámbar `#F59E0B` y azul `#007AFF`

### Pantalla de entrada — Animación Civitas (GlobeAnimation)
Al cargar la app, antes de la navegación principal, se muestra una animación de entrada con Globe.gl:
- Globo 3D terrestre (imagen nocturna, atmósfera ámbar) arranca con vista Atlántica y auto-rotación
- Logo Civitas aparece centrado y vuela a la esquina superior izquierda
- Zoom hacia España (altitude 0.75) y aparición escalonada de 8 citizen queries (burbujas flotantes con preguntas sobre presupuestos autonómicos)
- Rings de pulso dorado sobre las 3 comunidades indexadas; arcos animados conectando queries a nodos
- Panel de insights con 5 KPIs (consulta activa, fragmentos RAG, latencia, coherencia, coste)
- Zoom-out final a vista Atlántica con auto-rotación reanudada + tagline + botón CTA
- Botón "Saltar →" disponible a los 3s para usuarios que ya conocen el producto

### Estructura de navegación
- **Top nav**: 3 secciones — CIUDADANO, COMPLIANCE, MANTENIMIENTO
- **MANTENIMIENTO** tiene 6 sub-tabs:
  - **Sistema**: métricas en tiempo real (`/api/metrics` + `/api/health`)
  - **Documentos**: lista real de PDFs indexados + upload de nuevos PDFs
  - **Vectores**: scatter 3D Plotly con datos reales de `/api/vectores`
  - **Cómo funciona**: diagrama del pipeline RAG con parámetros reales
  - **Chat Técnico**: chat con visualización de fases RAG + chunks recuperados reales
  - **Insights**: tag cloud de temas, log de evaluaciones y alertas (desde `/api/metrics`)

### Chat
- Llamadas reales a `POST /api/chat`; fuentes mostradas como pills bajo cada respuesta
- Thumbs up/down (`👍`/`👎`) con `PATCH /api/feedback/{id}` bajo cada respuesta del asistente
- Spinner durante la espera; `sesion_id` persistido en ref durante la sesión

---

## COMANDOS CLAVE

```bash
# Arrancar backend
bash start_api.sh
# → disponible en http://localhost:8000
# → Swagger/docs en http://localhost:8000/docs

# Arrancar frontend
cd frontend && npm run dev
# → disponible en http://localhost:5173 (o 5174 si 5173 está ocupado)

# Reindexar (añadir PDFs nuevos a data/raw/ primero)
venv/bin/python pipeline.py

# Reconstruir base de datos vectorial desde cero
rm -rf data/vectordb/ data/processed/datos_extraidos.json
venv/bin/python pipeline.py

# Reconstruir venv si se rompe
rm -rf venv
/opt/homebrew/bin/python3.11 -m venv venv
venv/bin/pip install -r requirements.txt

# Conectar al servidor Hetzner
ssh root@46.224.81.240

# Actualizar servidor tras push
cd contratos_licitaciones && git pull
```

---

## DECISIONES TÉCNICAS IMPORTANTES

### PCA en lugar de UMAP

| | UMAP | PCA (elegida) |
|--|------|--------------|
| Librería | umap-learn | scikit-learn (ya instalada) |
| Compatibilidad | **Rota en Python 3.11**: busca `pkg_resources` que no existe | Estable, sin dependencias extra |
| Velocidad | ~10s para 543 vectores | Instantáneo |
| Calidad visual | Mejor preservación topológica local | Suficiente para visualización exploratoria |

**Conclusión**: umap-learn 0.5.x depende de `pkg_resources` (parte de `setuptools` antiguo), que Python 3.11 elimina. Se probó sin éxito. PCA de scikit-learn es suficiente para el objetivo de visualización del proyecto.

### Python 3.11 en lugar de 3.14

Python 3.14.3 fue descartado porque estas librerías claves del proyecto no son compatibles:
- **ChromaDB**: fallos en compilación de dependencias nativas
- **FastAPI** + **tenacity**: incompatibilidades con internos del intérprete
- **opentelemetry**: dependencia transitiva de ChromaDB, falla en 3.14

**Solución**: venv creado con `/opt/homebrew/bin/python3.11` — versión estable con soporte completo de todas las dependencias.

### Plotly con Vite — import directo

`react-plotly.js` usa `createPlotlyComponent()` que falla con Vite porque intenta acceder a objetos del DOM durante el import. La solución correcta:

```jsx
// CORRECTO — import directo del bundle minificado
import Plotly from 'plotly.js/dist/plotly.min.js'

// Usar Plotly.newPlot() dentro de useEffect(), no createPlotlyComponent()
useEffect(() => {
  Plotly.newPlot(divRef.current, traces, layout, config)
  return () => Plotly.purge(divRef.current)
}, [puntos])
```

**No usar** `createPlotlyComponent` de `react-plotly.js` con Vite — produce errores de bundling.

### Recuperación balanceada por comunidad

El corpus está desbalanceado: Andalucía tiene 890 chunks vs 87 de Madrid. Con top-6 global, las preguntas comparativas devuelven principalmente chunks de Andalucía, sesgando la respuesta.

**Solución** — `busqueda_balanceada()` en `api/server.py`:

| Caso | Estrategia | Resultado |
|------|-----------|-----------|
| 0 comunidades, no comparativa | top-6 global | `"global"` |
| 1 comunidad detectada | top-6 filtrado con `where fuente` | `"filtrado_<comunidad>"` |
| 2 comunidades detectadas | top-3 de cada una (6 total) | `"balanceado_2comunidades"` |
| 3 comunidades o comparativa general | top-2 de cada comunidad | `"balanceado_3comunidades"` |
| Filtro falla (exception ChromaDB) | fallback a top-6 global | `"global_fallback"` |

La estrategia usada se guarda en SQLite (`estrategia_busqueda`) y se devuelve en la respuesta JSON para auditoría. La detección de comunidades usa `KEYWORDS_COMUNIDADES` (keywords por comunidad) y `KEYWORDS_COMPARATIVA` (verbos de comparación).

### HyDE — implementado y luego eliminado

HyDE (Hypothetical Document Embedding) fue implementado para reducir el mismatch entre el lenguaje natural del usuario y el vocabulario técnico de los PDFs. Se generaba un fragmento hipotético de documento oficial con GPT-4o-mini y se embebía ese fragmento en lugar de la pregunta.

**Motivo de eliminación**: Los nuevos PDFs son documentos narrativos publicados directamente por las comunidades autónomas, escritos ya en lenguaje accesible. El mismatch de vocabulario desapareció, haciendo HyDE innecesario y añadiendo una llamada extra a la API sin beneficio.

---

## ESTADO ACTUAL (abril 2026)

### Completado y funcional
- [x] Pipeline RAG completo (extracción, chunking, narrativización de tablas, embedding, búsqueda)
- [x] API REST con FastAPI (endpoints chat, vectores, health, metrics, documentos, upload, feedback)
- [x] Interfaz web React con modo ciudadano y técnico
- [x] Visualización 3D de la base vectorial con PCA
- [x] Panel técnico RAG en tiempo real (timeline de fases + chunks con similitud)
- [x] Chat con preguntas sugeridas rotativas y cita automática de fuentes
- [x] Despliegue en VPS Hetzner — Nginx sirve frontend compilado, FastAPI como servicio systemd
- [x] Narrativizador de tablas: `pipeline.py` convierte tablas a prosa con GPT-4o antes de vectorizar
- [x] Logging anónimo de conversaciones en SQLite (`data/logs/conversaciones.db`) — 22 columnas
- [x] Banner de aviso legal prominente en el frontend
- [x] Citas de fuente con documento y página al pie de cada respuesta
- [x] Nombres de documentos legibles en citas de fuente
- [x] Fórmula de similitud coseno unificada: (2-dist)/2*100
- [x] Normalizador de texto plano: `src/normalizador.py`
- [x] HyDE eliminado — flujo simplificado con embedding directo de la pregunta
- [x] Recuperación balanceada por comunidad autónoma — evita sesgo del corpus desbalanceado

### Pendiente
- [ ] Ampliar corpus de Madrid (87 chunks actuales vs 890 de Andalucía)
- [ ] Modalidad de audio con transcripción — poder hablar al chat (Web Speech API o Whisper)
- [ ] Bloque B completo: detección de fraude en licitaciones con Isolation Forest

---

## LIMITACIONES CONOCIDAS

### Cobertura de comunidades autónomas
La base de datos solo cubre las CCAA cuyos PDFs están en `data/raw/`. Preguntas sobre otras comunidades no tendrán datos. El sistema informa explícitamente al usuario qué comunidades están disponibles cuando no puede responder.

### Páginas escaneadas
Páginas 48-50 del PDF de Madrid son imágenes. pdfplumber no extrae texto. Requeriría OCR (pytesseract) — no implementado.

### Pipeline re-narrativiza todo cuando la vectordb está vacía
Si se borra `data/vectordb/` pero se conserva `data/processed/datos_extraidos.json`, el pipeline re-usa los datos extraídos pero re-narrativiza todas las tablas. No guarda estado entre la fase de narrativización y la de vectorización, lo que genera coste API innecesario en reconstrucciones.

### Chunks de tablas sin límite de tamaño
Tablas muy grandes (PDFs con más de ~800 páginas) pueden producir chunks que superan el límite de 8192 tokens del modelo `text-embedding-3-small`. El pipeline no trunca ni fragmenta chunks de tabla.

### Corpus desbalanceado — sesgo en comparativas
Andalucía tiene 890 chunks vs 87 de Madrid. En preguntas comparativas el retriever tiende a devolver más chunks de Andalucía, sesgando la respuesta. La solución es ampliar el corpus de Madrid o implementar recuperación por comunidad explícita.

### Lo que funciona bien
- Preguntas directas con dato concreto ("cuánto a Sanidad")
- Comparativas entre comunidades con PDFs indexados
- Preguntas de contexto narrativo
- Cita automática de página fuente en cada respuesta

---

## BLOQUE B — ESTADO Y PLAN

> **DECISIÓN DE SPRINT**: El Bloque B queda como objetivo aspiracional. No se implementará en el sprint actual. El foco está en Bloque A.

### Objetivo
Detectar contratos públicos españoles con patrones de fraude usando ML no supervisado.

### Pipeline planificada (equipo de 4 personas)
1. Ingesta de datos — descarga contratos de PLACE/datos.gob.es
2. **Procesamiento y normalización** ← PARTE DE GINES
3. Feature Engineering + ML (Isolation Forest)
4. Visualización / Dashboard de alertas

### Notas de exploración previa
- PLACE API requiere certificado digital → descartada para prototipo
- Alternativa viable: `datos.gob.es` — datasets CSV de contratos del Ministerio de Hacienda, descarga directa sin auth
- Ningún script de Bloque B está operativo

### Features de fraude planificadas
- `ratio_concentracion`: % contratos del organismo que gana esta empresa
- `cerca_umbral`: importe entre 45.000-50.000€ (fraccionamiento)
- `baja_concurrencia`: menos de 2 licitadores
- `modificado_significativo`: modificación > 20% precio original
- `dias_adjudicacion_ratio`: velocidad adjudicación vs media

### Algoritmo central
Isolation Forest (`sklearn.ensemble`) — no supervisado, no requiere datos etiquetados, detecta anomalías estadísticas en espacio n-dimensional de features.

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
| Reducción dimensional | PCA (sklearn) | UMAP incompatible con Python 3.11 — ver decisiones técnicas |
| Python | 3.11 | 3.14 incompatible con ChromaDB y FastAPI — ver decisiones técnicas |
| Frontend | Standalone HTML (React CDN + Babel) | Sin build step en dev, desplegable sin Node en servidor; Vite solo para proxy en local |
| HyDE | Eliminado — embed directo de la pregunta | Los nuevos PDFs son narrativos; mismatch de vocabulario ya no existe |
| Logging SQLite | `data/logs/conversaciones.db` excluido de git | Datos de servidor y local son distintos; fichero binario mutable |
| Similitud coseno | (2-distancia)/2*100 | ChromaDB devuelve distancias 0-2, no 0-1. Esta fórmula da porcentaje real |
| Normalización texto | Python puro antes del chunking | Limpia artefactos del PDF sin coste de API. Solo tablas usan GPT-4o |
| Chunks recuperados | n=6 | Equilibrio entre cobertura y tamaño de contexto enviado al LLM |

---

## INFRAESTRUCTURA

### Servidor VPS Hetzner
- **IP**: 46.224.81.240
- **Acceso SSH**: `ssh root@46.224.81.240`
- **Ruta del proyecto**: `/root/contratos_licitaciones`
- **Estado**: Activo y en producción — Nginx sirviendo frontend compilado + proxy a FastAPI en systemd
- **Configuración**: `.env` con OPENAI_API_KEY configurada
- **URL pública**: http://46.224.81.240

### Flujo de actualización
```
git push (local)
  ↓
ssh root@46.224.81.240
  ↓
cd contratos_licitaciones && git pull
  ↓
cd frontend && npm run build    ← siempre — genera frontend/dist/
  ↓
systemctl restart fastapi       ← siempre — recarga api/server.py
```

---

## DESPLIEGUE EN SERVIDOR

**DESPLIEGUE EN SERVIDOR HETZNER (completado abril 2026):**

### Pasos realizados
1. git pull — bajó 25 archivos nuevos (frontend/ + api/)
2. Instalación Python 3.11 via deadsnakes PPA:
   ```
   apt install software-properties-common -y
   add-apt-repository ppa:deadsnakes/ppa -y
   apt update
   apt install python3.11 python3.11-venv -y
   ```
3. Recreación venv con Python 3.11:
   ```
   rm -rf venv && python3.11 -m venv venv && venv/bin/pip install -r requirements.txt
   ```
4. Instalación Node.js 20 y build del frontend:
   ```
   curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
   apt install nodejs -y
   cd frontend && npm install && npm run build && cd ..
   ```
5. Instalación y configuración Nginx:
   ```
   apt install nginx -y
   ```
   Configuración en `/etc/nginx/sites-available/presupuestos`:
   - `location /` → sirve `frontend/dist/` (archivos estáticos compilados con `npm run build`)
   - `location /api/` → proxy a `localhost:8000/api/` (FastAPI, que ya tiene el prefijo `/api/`)

6. FastAPI como servicio systemd:
   - Archivo: `/etc/systemd/system/fastapi.service`
   - `systemctl enable fastapi && systemctl start fastapi`

7. Permisos: `chmod 755 /root && chmod -R 755 frontend/dist`

### Estado actual del servidor
- **FastAPI**: activo como servicio systemd, arranca automáticamente al reiniciar
- **Nginx**: activo, sirve en puerto 80; config activa en `/etc/nginx/sites-enabled/presupuestos`; sirve `frontend/dist/`
- **URL pública**: http://46.224.81.240

### Comandos útiles en el servidor
```bash
# Ver logs FastAPI
journalctl -u fastapi -f

# Reiniciar FastAPI
systemctl restart fastapi  

# Reiniciar Nginx
systemctl restart nginx

# Recompilar frontend
cd /root/contratos_licitaciones/frontend && npm run build

# Ver estado servicios
systemctl status fastapi && systemctl status nginx
```

---

## PROBLEMAS RESUELTOS — HISTORIAL

**2026-04-30 — Globe.gl animation upgrade — citizen queries, rings, arcs y final limpio**

`GlobeAnimation` en `frontend/index.html` completamente reescrita. Nueva secuencia de 5 actos: 8 citizen queries distribuidas por España aparecen escalonadas, rings de pulso dorado sobre comunidades indexadas (Globe.gl `.ringsData()`), arcos animados conectando queries a nodos, panel de insights con 5 KPIs, zoom-out final a vista Atlántica con auto-rotación reanudada. Puntos flat (sin pilares), arcos finos, animación `queryPop`. Limpieza completa del globo (puntos + arcos + rings) antes del finale.

---

**2026-04-28 — Rename a Civitas, respuestas JSON con Plotly, rediseño InsightsTab**

Proyecto renombrado a **Civitas** en toda la interfaz. Las respuestas del chat ahora pueden incluir gráficos Plotly embebidos (JSON detectado en respuesta → renderizado inline). InsightsTab rediseñada. Métricas del backend corregidas en `api/server.py`.

---

**2026-04-29 — Recuperación balanceada por comunidad**

Implementada `busqueda_balanceada()` en `api/server.py`. Resuelve el sesgo del corpus desbalanceado en preguntas comparativas. Ver detalles en Decisiones técnicas → Recuperación balanceada por comunidad.

---

**2026-04-26 — Eliminación de HyDE y simplificación del pipeline**

- **HyDE eliminado**: con el cambio a documentos narrativos de las CCAA, el mismatch de vocabulario desapareció. Se eliminó la generación del fragmento hipotético y el fichero `data/processed/ejemplos_hyde.json`. El endpoint `/chat` ahora embebe la pregunta directamente. El campo `hipotesis_hyde` en SQLite se conserva (compatibilidad con logs históricos) pero se registra como `null`. Ver detalles en Decisiones técnicas → HyDE.
- **Corpus actualizado**: sustituidos documentos anteriores por PDFs narrativos de CCAA. Corpus actual: `andalucia.pdf`, `castillayleon.pdf`, `presupuestos_generales_2026.pdf`, `resumen_ingresos_y_gastos.pdf`.
- **n_results = 6**: valor restaurado tras haberse subido temporalmente a 12 durante las pruebas con HyDE.

---

**2026-04-20 — Nombres legibles, similitud coseno corregida y normalizador de texto**

- **Nombres de documento legibles** (`api/server.py`): diccionario `NOMBRES_DOCUMENTOS` mapea filename → nombre legible. Fallback: nombre sin extensión.
- **Fórmula de similitud unificada** (`api/server.py`): ChromaDB coseno devuelve distancias 0-2, no 0-1. Corregido de `1 - distance` a `(2 - distance) / 2 * 100`. Ver Decisiones técnicas → Similitud coseno.
- **Normalizador de texto plano** (`src/normalizador.py` + `pipeline.py`): `normalizar_texto()` elimina artefactos PDF (guiones de fin de línea, cabeceras repetitivas, líneas de número de página). Aplicado sobre chunks de tipo "texto" tras el chunking.

---

**2026-04-20 — Logging SQLite, sesion_id anónimo, banner legal y citas de fuente**

- **Logging SQLite** (`api/server.py`): cada conversación se registra en `data/logs/conversaciones.db` con sesion_id UUID, timestamp, pregunta, respuesta, score, chunks y fuentes. Excluida de git.
- **sesion_id anónimo** (`frontend/index.html`): UUID generado con `crypto.randomUUID()` al inicio de la sesión, incluido en cada POST /chat. No persiste en storage.
- **Banner aviso legal** (`frontend/index.html`): modal prominente con texto legal completo, no desaparece hasta click explícito.
- **Citas de fuente** (`api/server.py`): el backend deduplica chunks por documento y devuelve `fuentes: [{documento, paginas: [...]}]`. El frontend lo renderiza al pie de cada respuesta.

---

## ERRORES CONOCIDOS Y SOLUCIONES

| Error | Causa | Solución |
|-------|-------|---------|
| `ModuleNotFoundError: pkg_resources` al importar umap-learn | umap-learn 0.5.x depende de setuptools antiguo, eliminado en Python 3.11 | Reemplazar UMAP por PCA de scikit-learn en `api/server.py` |
| ChromaDB y FastAPI fallan con Python 3.14.3 | 3.14 aún en desarrollo, dependencias nativas sin soporte | Recrear venv con `/opt/homebrew/bin/python3.11` |
| `react-plotly.js` da error de bundling con Vite | `createPlotlyComponent()` accede al DOM en tiempo de import | Usar `window.Plotly.newPlot()` directamente en `useEffect()` (Plotly cargado via CDN) |
| `python`/`python3` en terminal no encuentra librerías del proyecto | Claude Code o macOS apunta al Python global de Homebrew | Usar siempre `venv/bin/python` y `venv/bin/pip` de forma explícita |
| Frontend en puerto distinto al esperado | Si 5173 está ocupado, Vite auto-incrementa a 5174 | Normal — el puerto configurado es 5173, usar el que muestre Vite al arrancar |

---

## PRÓXIMOS PASOS IDENTIFICADOS

1. Ampliar corpus de Madrid: indexar más PDFs de la Comunidad de Madrid para equilibrar los 890 chunks de Andalucía
2. Modalidad de audio con transcripción: poder hablar al chat (Web Speech API o Whisper)
3. *(Aspiracional — fuera de sprint)* Bloque B: detección de fraude en licitaciones con Isolation Forest

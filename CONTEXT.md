# PROYECTO: Plataforma de Transparencia Ciudadana
## Contexto para asistente IA — Master IA ISDI 2026

---

## IDENTIDAD DEL PROYECTO

Sistema RAG de transparencia pública con dos bloques:
- **Bloque A** (COMPLETO y FUNCIONAL con interfaz web): Chatbot que responde preguntas sobre presupuestos públicos en lenguaje natural
- **Bloque B** (PENDIENTE): Detección de anomalías en licitaciones públicas españolas

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
| Backend | FastAPI 0.115 + Uvicorn | puerto 8000 |
| Frontend | React 19 + Vite 8 + Tailwind 4 | puerto 5173 (o 5174 si está ocupado) |
| Visualización | plotly.js 3.x | importado directo — ver decisiones técnicas |
| OS / entorno | macOS, VSCode | — |

> **IMPORTANTE sobre Python**: usar siempre `venv/bin/python` y `venv/bin/pip`.
> Claude Code y terminales macOS pueden apuntar al Python global de Homebrew sin las librerías del proyecto.

---

## BLOQUE A — ARQUITECTURA RAG COMPLETA

### Pipeline offline (`pipeline.py` orquesta todo)
```
data/raw/*.pdf
  → src/extractor.py        → data/processed/datos_extraidos.json
  → src/chunker.py          → data/processed/chunks.json
  → src/narrativizador.py   → data/processed/chunks_narrativizados.json  (chunks tipo tabla → prosa con GPT-4o)
  → src/embedder.py         → data/vectordb/ (ChromaDB)
```

### Pipeline online (`src/chatbot.py` CLI / `api/server.py` HTTP)
```
pregunta usuario
  → embed pregunta (OpenAI text-embedding-3-small)
  → ChromaDB query (top-6 chunks, similitud coseno)
  → prompt = contexto_chunks + pregunta
  → GPT-4o-mini → respuesta con cita de página
```

### Parámetros clave
- Chunk size: 500 tokens
- Solapamiento: 50 tokens (10%)
- Tablas: 1 chunk por tabla completa (cabecera+filas como "col: valor | col: valor")
- Chunks recuperados en query: n=6
- Total vectores actuales: **543** (239 tablas narrativizadas con GPT-4o + 304 chunks de texto plano)

### Documentos indexados
| Fichero | Descripción | Páginas |
|---------|-------------|---------|
| `presupuestos_generales_2026.pdf` | Comunidad de Madrid 2026 | 50 |
| `resumen_ingresos_y_gastos.pdf` | Resumen ingresos/gastos Madrid | 3 |
| `ResumenEjecutivo2026.pdf` | Presupuestos todas las CC.AA. España 2026 | 241 |

### Procesamiento incremental
`pipeline.py` detecta si un PDF ya está en ChromaDB por la clave `fuente`. Si existe → salta. Si no → procesa y añade. No duplica vectores.

---

## ESTRUCTURA DE CARPETAS

```
Isdi-presupuestos/
├── api/
│   ├── __init__.py
│   └── server.py              ← FastAPI — endpoints /chat /vectores /health
├── data/
│   ├── raw/                   ← PDFs fuente (NUNCA modificar)
│   ├── processed/             ← JSONs intermedios (regenerables con pipeline.py)
│   └── vectordb/              ← ChromaDB (regenerable con pipeline.py)
├── frontend/                  ← React + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx            ← Raíz: header, tabs, modo ciudadano/técnico
│   │   ├── components/
│   │   │   ├── ChatPanel.jsx  ← Chat con el RAG, input, burbujas de mensaje
│   │   │   ├── TechPanel.jsx  ← Panel técnico RAG: timeline de fases + chunks
│   │   │   └── VectorMap.jsx  ← Visualización 3D Plotly de la base vectorial
│   │   ├── index.css          ← Variables CSS globales, dark theme
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js         ← puerto configurado: 5173
├── src/
│   ├── extractor.py           ← pdfplumber → JSON
│   ├── chunker.py             ← JSON → chunks con solapamiento
│   ├── narrativizador.py      ← chunks tipo tabla → texto narrativo en prosa con GPT-4o (→ chunks_narrativizados.json)
│   ├── embedder.py            ← chunks_narrativizados.json → vectores ChromaDB
│   ├── chatbot.py             ← interfaz conversacional terminal (legacy)
│   ├── procesador_tablas.py   ← script debug/inspección de tablas
│   └── descargador_licitaciones.py ← prototipo Bloque B (no integrado)
├── pipeline.py                ← orquestador Bloque A
├── start_api.sh               ← `source venv/bin/activate && uvicorn api.server:app --reload --port 8000`
├── requirements.txt           ← dependencias con versiones exactas
├── .env                       ← OPENAI_API_KEY (NUNCA a Git)
└── .gitignore                 ← venv/, __pycache__/, .env
```

---

## API REST (Bloque A — backend)

### Stack
- Framework: FastAPI 0.115
- Servidor: Uvicorn (ASGI), puerto 8000
- CORS: `allow_origins=["*"]` (acepta frontend local y producción)
- Arranque: `bash start_api.sh`

### Endpoints

#### POST /chat
Responde preguntas sobre presupuestos usando el pipeline RAG completo.

**Request**
```json
{ "pregunta": "¿Cuánto destina Madrid a Sanidad?", "historial": [] }
```
**Response**
```json
{
  "respuesta": "Texto generado por GPT-4o-mini...",
  "chunks": [
    { "texto": "...", "fuente": "presupuestos_generales_2026.pdf", "pagina": 12, "distancia": 0.23 }
  ]
}
```
**Lógica**: embed pregunta → ChromaDB top-6 → prompt + GPT-4o-mini (temperature=0.3)

#### GET /vectores
Devuelve todos los vectores de ChromaDB reducidos a 3D con **PCA** (ya no UMAP).

**Response**
```json
{
  "puntos": [
    { "x": 1.23, "y": -0.45, "z": 2.11, "texto": "...", "fuente": "...", "pagina": 5 }
  ]
}
```
**Nota**: La reducción PCA es instantánea (a diferencia de UMAP que tardaba ~10s).

#### GET /health
Comprueba que el servidor y ChromaDB están operativos.

**Response**
```json
{ "status": "ok", "vectores": 543 }
```

---

## FRONTEND — Interfaz Web

### Stack
- React 19 + Vite 8 + Tailwind CSS 4
- Dark theme con variables CSS (definidas en `src/index.css`)
- Visualización 3D: `plotly.js` importado directamente — ver decisiones técnicas

### Componentes principales

| Componente | Descripción |
|-----------|-------------|
| `App.jsx` | Layout principal: header, toggle ciudadano/técnico, tabs Chat/Vectores |
| `ChatPanel.jsx` | Interfaz de chat: burbujas, pantalla de bienvenida, sugerencias, input |
| `TechPanel.jsx` | Panel lateral técnico: timeline de fases RAG + chunks recuperados con similitud |
| `VectorMap.jsx` | Visualización 3D Plotly: nube de puntos con color por documento, hover con texto |

### Dos modos de usuario
- **Ciudadano**: solo muestra el chat (panel técnico oculto)
- **Técnico**: chat a 60% ancho + TechPanel a 40% mostrando el proceso RAG en tiempo real

### Dos tabs
- **Chat**: interfaz conversacional con el RAG
- **Base de Datos Vectorial**: visualización 3D interactiva de los 543 embeddings

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

# Ejecutar chatbot en terminal (legacy)
venv/bin/python3 src/chatbot.py

# Reindexar (añadir PDFs nuevos a data/raw/ primero)
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

---

## ESTADO ACTUAL (abril 2026)

### Completado y funcional
- [x] Pipeline RAG completo (extracción, chunking, embedding, búsqueda)
- [x] API REST con FastAPI (3 endpoints)
- [x] Interfaz web React con modo ciudadano y técnico
- [x] Visualización 3D de la base vectorial con PCA
- [x] Panel técnico RAG en tiempo real (timeline de fases + chunks con similitud)
- [x] Chat con preguntas sugeridas y cita automática de fuentes
- [x] Despliegue en VPS Hetzner — Nginx sirve frontend compilado, FastAPI como servicio systemd
- [x] Camino B — narrativizador de tablas: `src/narrativizador.py` convierte las 239 tablas a prosa con GPT-4o antes de vectorizar

### Pendiente
- [ ] **URGENTE — reconstruir base de datos vectorial**: la BD actual mezcla vectores narrativizados y no narrativizados (pipeline detectó solo 1 doc nuevo y lo narrativizó; los docs anteriores siguen vectorizados sin narrativización). Solución: borrar `data/vectordb/` y re-ejecutar `pipeline.py` completo desde cero.
- [ ] Sección de administración para subir nuevos PDFs desde la web (sin usar terminal)
- [ ] Interfaces más gráficas: mejorar visualizaciones, dashboards y UX general
- [ ] Modalidad de audio con transcripción — poder hablar al chat (Web Speech API o Whisper)
- [ ] Bloque B completo: detección de fraude en licitaciones con Isolation Forest

---

## LIMITACIONES CONOCIDAS

### Tablas — vocabulario técnico
Las tablas se vectorizan como texto con formato "cabecera: valor | cabecera: valor". Funciona para preguntas directas pero falla en:
- Rankings entre todas las CC.AA. ("cuál tiene mayor presupuesto")
- Comparativas que cruzan múltiples secciones del documento
- **Causa**: mismatch entre términos técnicos del PDF ("empleos no financieros") y lenguaje natural ("presupuesto total")

**Solución diseñada — Camino B (no implementada)**: llamar API Claude/GPT para convertir cada tabla en texto narrativo ANTES de vectorizar. Normaliza el vocabulario.

### Páginas escaneadas
Páginas 48-50 del PDF de Madrid son imágenes. pdfplumber no extrae texto. Requeriría OCR (pytesseract) — no implementado.

### Lo que funciona bien
- Preguntas directas con dato concreto ("cuánto a Sanidad")
- Comparativas entre 2 comunidades específicas mencionadas explícitamente
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
- Alternativa viable: `datos.gob.es` — datasets CSV de contratos del Ministerio de Hacienda, descarga directa sin auth
- `src/descargador_licitaciones.py` es exploración inicial, no integrado en pipeline
- Ningún script de Bloque B está operativo todavía

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
| Frontend | React + Vite | Más flexible que Streamlit para la interfaz dual ciudadano/técnico |

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
(si hay cambios en frontend) cd frontend && npm run build
  ↓
(si hay cambios en backend) pkill uvicorn && bash start_api.sh &
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
   - `location /` → sirve `frontend/dist/` (archivos estáticos)
   - `location /api/` → proxy a `localhost:8000` (FastAPI)

6. FastAPI como servicio systemd:
   - Archivo: `/etc/systemd/system/fastapi.service`
   - `systemctl enable fastapi && systemctl start fastapi`

7. Permisos: `chmod 755 /root && chmod -R 755 frontend/dist`

### Estado actual del servidor
- **FastAPI**: activo como servicio systemd, arranca automáticamente al reiniciar
- **Nginx**: activo, sirve en puerto 80
- **URL pública**: http://46.224.81.240
- **API_BASE**: corregido a rutas relativas (`/api/`) en `ChatPanel.jsx` y `VectorMap.jsx` — ya recompilado y desplegado.

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

| Error | Causa | Solución |
|-------|-------|---------|
| `ModuleNotFoundError: pkg_resources` al importar umap-learn | umap-learn 0.5.x depende de setuptools antiguo, eliminado en Python 3.11 | Reemplazar UMAP por PCA de scikit-learn en `api/server.py` |
| ChromaDB y FastAPI fallan con Python 3.14.3 | 3.14 aún en desarrollo, dependencias nativas sin soporte | Recrear venv con `/opt/homebrew/bin/python3.11` |
| `react-plotly.js` da error de bundling con Vite | `createPlotlyComponent()` accede al DOM en tiempo de import | Importar `plotly.js/dist/plotly.min.js` directamente y usar `Plotly.newPlot()` en `useEffect()` |
| `python`/`python3` en terminal no encuentra librerías del proyecto | Claude Code o macOS apunta al Python global de Homebrew | Usar siempre `venv/bin/python` y `venv/bin/pip` de forma explícita |
| Frontend en puerto distinto al esperado | Si 5173 está ocupado, Vite auto-incrementa a 5174 | Normal — el puerto configurado es 5173, usar el que muestre Vite al arrancar |

---

## PRÓXIMOS PASOS IDENTIFICADOS

1. **URGENTE**: reconstruir base de datos vectorial — borrar `data/vectordb/` y re-ejecutar `pipeline.py` completo para que todos los documentos queden vectorizados con narrativización de tablas
2. Sección administración: formulario web para subir PDFs sin usar terminal
3. Interfaces más gráficas: mejorar visualizaciones, dashboards y UX general
4. Modalidad de audio con transcripción: poder hablar al chat (Web Speech API o Whisper)
5. Bloque B: descargar dataset CSV de contratos de `datos.gob.es` y construir `src/limpiador.py` (parte de Gines)
6. Bloque B: Feature engineering + Isolation Forest

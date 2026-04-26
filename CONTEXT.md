# PROYECTO: Plataforma de Transparencia Ciudadana
## Contexto para asistente IA — Master IA ISDI 2026

---

## IDENTIDAD DEL PROYECTO

Sistema RAG de transparencia pública con dos bloques:
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
| Backend | FastAPI 0.115 + Uvicorn | puerto 8000 |
| Frontend | React 19 + Vite 8 + Tailwind 4 | puerto 5173 (o 5174 si está ocupado) |
| Visualización | plotly.js 3.x | importado directo — ver decisiones técnicas |
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
  → ChromaDB query (top-6 chunks, similitud coseno)
  → prompt = contexto_chunks + pregunta
  → GPT-4o-mini → respuesta con cita de página
```

### Parámetros clave
- Chunk size: 500 tokens
- Solapamiento: 50 tokens (10%)
- Tablas: 1 chunk por tabla, narrativizado a prosa con GPT-4o antes de vectorizar
- Chunks recuperados en query: **n=6**
- Total vectores actuales: **pendiente de reconstrucción** (BD debe regenerarse con los nuevos PDFs)

### Documentos indexados
| Fichero | Descripción | Notas |
|---------|-------------|-------|
| `presupuestos_generales_2026.pdf` | Presupuestos Generales Madrid 2026 | 50 páginas |
| `resumen_ingresos_y_gastos.pdf` | Resumen ingresos/gastos Madrid | 3 páginas |
| `andalucia.pdf` | Presupuestos Comunidad de Andalucía 2026 | Narrativo CCAA |
| `castillalamancha.pdf` | Presupuestos Castilla-La Mancha 2026 | Narrativo CCAA |
| `castillayleon.pdf` | Presupuestos Castilla y León 2026 | Narrativo CCAA |

> Los nuevos PDFs (`andalucia.pdf`, `castillalamancha.pdf`, `castillayleon.pdf`) son documentos narrativos publicados directamente por las comunidades autónomas. Su vocabulario ya es cercano al lenguaje natural, lo que simplificó el pipeline (eliminación de HyDE).

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
│   ├── normalizador.py        ← ÚNICO MÓDULO ACTIVO: limpieza de texto plano pre-chunking
│   ├── chatbot.py             ← legacy — interfaz conversacional terminal (no usado en flujo)
│   ├── chunker.py             ← legacy — lógica reimplementada en pipeline.py
│   ├── extractor.py           ← legacy — lógica reimplementada en pipeline.py
│   ├── narrativizador.py      ← legacy — lógica reimplementada en pipeline.py
│   ├── embedder.py            ← legacy — lógica reimplementada en pipeline.py
│   └── procesador_tablas.py   ← script debug/inspección de tablas
├── pipeline.py                ← orquestador Bloque A (todo el procesamiento aquí)
├── start_api.sh               ← `source venv/bin/activate && uvicorn api.server:app --reload --port 8000`
├── requirements.txt           ← dependencias con versiones exactas
├── .env                       ← OPENAI_API_KEY (NUNCA a Git)
└── .gitignore                 ← venv/, __pycache__/, .env
```

> **Nota sobre src/**: Solo `normalizador.py` está activo. El resto son módulos históricos cuya lógica fue absorbida por `pipeline.py`. Se mantienen como referencia pero no forman parte del flujo.

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
**Lógica**: embed pregunta directamente → ChromaDB top-6 → prompt + GPT-4o-mini (temperature=0.3)

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
- **Base de Datos Vectorial**: visualización 3D interactiva de los embeddings

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

### HyDE — implementado y luego eliminado

HyDE (Hypothetical Document Embedding) fue implementado para reducir el mismatch entre el lenguaje natural del usuario y el vocabulario técnico de los PDFs. Se generaba un fragmento hipotético de documento oficial con GPT-4o-mini y se embebía ese fragmento en lugar de la pregunta.

**Motivo de eliminación**: Los nuevos PDFs son documentos narrativos publicados directamente por las comunidades autónomas, escritos ya en lenguaje accesible. El mismatch de vocabulario desapareció, haciendo HyDE innecesario y añadiendo una llamada extra a la API sin beneficio.

---

## ESTADO ACTUAL (abril 2026)

### Completado y funcional
- [x] Pipeline RAG completo (extracción, chunking, narrativización de tablas, embedding, búsqueda)
- [x] API REST con FastAPI (3 endpoints)
- [x] Interfaz web React con modo ciudadano y técnico
- [x] Visualización 3D de la base vectorial con PCA
- [x] Panel técnico RAG en tiempo real (timeline de fases + chunks con similitud)
- [x] Chat con preguntas sugeridas y cita automática de fuentes
- [x] Despliegue en VPS Hetzner — Nginx sirve frontend compilado, FastAPI como servicio systemd
- [x] Narrativizador de tablas: `pipeline.py` convierte tablas a prosa con GPT-4o antes de vectorizar
- [x] Logging anónimo de conversaciones en SQLite (`data/logs/conversaciones.db`)
- [x] Banner de aviso legal en el frontend
- [x] Citas de fuente con documento y página al pie de cada respuesta
- [x] Nombres de documentos legibles en citas de fuente
- [x] Fórmula de similitud coseno unificada: (2-dist)/2*100
- [x] Normalizador de texto plano: `src/normalizador.py`
- [x] HyDE eliminado — flujo simplificado con embedding directo de la pregunta

### Pendiente
- [ ] **Reconstruir base de datos vectorial** con los nuevos PDFs (andalucia, castillalamancha, castillayleon) — borrar `data/vectordb/` y re-ejecutar `pipeline.py`
- [ ] Sección de administración para subir nuevos PDFs desde la web (sin usar terminal)
- [ ] Interfaces más gráficas: mejorar visualizaciones, dashboards y UX general
- [ ] Modalidad de audio con transcripción — poder hablar al chat (Web Speech API o Whisper)
- [ ] Bloque B completo: detección de fraude en licitaciones con Isolation Forest

---

## LIMITACIONES CONOCIDAS

### Cobertura de comunidades autónomas
La base de datos solo cubre las CCAA cuyos PDFs están en `data/raw/`. Preguntas sobre otras comunidades no tendrán datos. El sistema informa explícitamente al usuario qué comunidades están disponibles cuando no puede responder.

### Páginas escaneadas
Páginas 48-50 del PDF de Madrid son imágenes. pdfplumber no extrae texto. Requeriría OCR (pytesseract) — no implementado.

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
| Frontend | React + Vite | Más flexible que Streamlit para la interfaz dual ciudadano/técnico |
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

**2026-04-26 — Eliminación de HyDE y simplificación del pipeline**

- **HyDE eliminado** (`api/server.py` + `pipeline.py`): HyDE (Hypothetical Document Embedding) fue implementado para reducir el mismatch entre el vocabulario natural del usuario y el técnico de los PDFs. Con el cambio a documentos narrativos de las CCAA, ese mismatch desapareció. Se eliminó la generación del fragmento hipotético, la carga de ejemplos de vocabulario (`cargar_ejemplos_hyde()`), la extracción de ejemplos en pipeline (`extraer_ejemplos_hyde()`), y el fichero `data/processed/ejemplos_hyde.json`. El endpoint `/chat` ahora embebe la pregunta directamente. El campo `hipotesis_hyde` en SQLite se conserva en el schema (para no romper logs históricos) pero se registra como `null`.
- **Nuevos documentos narrativos**: sustituido `ResumenEjecutivo2026.pdf` por tres PDFs narrativos de comunidades autónomas (`andalucia.pdf`, `castillalamancha.pdf`, `castillayleon.pdf`). Actualizado `NOMBRES_DOCUMENTOS` en `api/server.py`.
- **n_results vuelve a 6**: se había subido a 12 temporalmente para mejorar cobertura comparativa con HyDE. Al simplificar el flujo se vuelve a 6 (equilibrio cobertura/tamaño de contexto).

---

**2026-04-20 — Nombres legibles, similitud coseno corregida y normalizador de texto**

- **Nombres de documento legibles** (`api/server.py`): añadido diccionario `NOMBRES_DOCUMENTOS` que mapea el nombre del fichero PDF al nombre legible. El campo `fuentes[].documento` en la respuesta JSON y en SQLite ahora muestra p.ej. "Presupuestos Generales Madrid 2026" en lugar de "presupuestos_generales_2026.pdf". Fallback: nombre del fichero sin extensión.
- **Fórmula de similitud unificada** (`api/server.py` + `TechPanel.jsx`): ChromaDB coseno devuelve distancias 0-2, no 0-1. Corregida la fórmula de `1 - distance` a `(2 - distance) / 2 * 100` en `ScoreBar` de TechPanel. En el backend, `score_medio` se guarda ahora como porcentaje real (0-100) y se añade `score_similitud_media` al JSON de respuesta.
- **Normalizador de texto plano** (`src/normalizador.py` + `pipeline.py`): nuevo módulo con función `normalizar_texto()` que elimina guiones de fin de línea, colapsa espacios, elimina puntos suspensivos, quita líneas de número de página y cabeceras repetitivas, y une líneas que no terminan en puntuación. Aplicado en `pipeline.py` sobre chunks de tipo "texto" tras el chunking.

**2026-04-20 — Logging, HyDE, banner legal y citas de fuente**

Implementados simultáneamente en una sesión:
- **HyDE** (`api/server.py`): antes de embeddar la pregunta se genera un fragmento hipotético de documento oficial con GPT-4o-mini (max_tokens=200, prompt estilo administrativo), y ese fragmento es el que se embeda. El resto del pipeline RAG es idéntico. *(Nota: eliminado el 2026-04-26 — ver entrada superior)*
- **Logging SQLite** (`api/server.py` + `data/logs/`): cada conversación se registra en `data/logs/conversaciones.db` con sesion_id anónimo (UUID), timestamp, pregunta, hipótesis HyDE, respuesta, score medio de similitud, núm. de chunks y fuentes JSON. La DB está excluida de git.
- **sesion_id anónimo** (`ChatPanel.jsx`): se genera un UUID con `crypto.randomUUID()` al montar el componente (lazy initializer de useState) y se incluye en cada POST /chat. No se persiste en storage.
- **Banner aviso legal** (`ChatPanel.jsx`): banner amarillo tenue al tope del panel de chat, con dos líneas de texto legal y botón ✕ para cerrar. Estado local, no persistido.
- **Citas de fuente** (`api/server.py` + `ChatPanel.jsx`): el backend deduplica chunks por documento y devuelve `fuentes: [{documento, paginas: [...]}]`. El frontend añade `fuentes` al objeto mensaje del asistente y lo renderiza al pie de cada burbuja con formato "📄 documento, p. X, Y".

| Error | Causa | Solución |
|-------|-------|---------|
| `ModuleNotFoundError: pkg_resources` al importar umap-learn | umap-learn 0.5.x depende de setuptools antiguo, eliminado en Python 3.11 | Reemplazar UMAP por PCA de scikit-learn en `api/server.py` |
| ChromaDB y FastAPI fallan con Python 3.14.3 | 3.14 aún en desarrollo, dependencias nativas sin soporte | Recrear venv con `/opt/homebrew/bin/python3.11` |
| `react-plotly.js` da error de bundling con Vite | `createPlotlyComponent()` accede al DOM en tiempo de import | Importar `plotly.js/dist/plotly.min.js` directamente y usar `Plotly.newPlot()` en `useEffect()` |
| `python`/`python3` en terminal no encuentra librerías del proyecto | Claude Code o macOS apunta al Python global de Homebrew | Usar siempre `venv/bin/python` y `venv/bin/pip` de forma explícita |
| Frontend en puerto distinto al esperado | Si 5173 está ocupado, Vite auto-incrementa a 5174 | Normal — el puerto configurado es 5173, usar el que muestre Vite al arrancar |

---

## PRÓXIMOS PASOS IDENTIFICADOS

1. **Reconstruir base de datos vectorial**: borrar `data/vectordb/` y re-ejecutar `pipeline.py` con los nuevos PDFs (andalucia, castillalamancha, castillayleon)
2. Sección administración: formulario web para subir PDFs sin usar terminal
3. Interfaces más gráficas: mejorar visualizaciones, dashboards y UX general
4. Modalidad de audio con transcripción: poder hablar al chat (Web Speech API o Whisper)
5. *(Aspiracional — fuera de sprint)* Bloque B: detección de fraude en licitaciones con Isolation Forest

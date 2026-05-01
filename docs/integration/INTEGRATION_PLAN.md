# Plan de Integración Diego ↔ Sito — Documento Maestro

**Inicio**: 2026-05-01
**Rama de trabajo**: `integration/diego-merge` (se creará en Fase 0)
**Repositorio fuente Diego**: https://github.com/diegovillavicencio94/contratos-licitaciones
**Repositorio destino**: https://github.com/sitomt/contratos_licitaciones
**Estado global**: 🟡 Bootstrap completado, fases pendientes

## Filosofía

Integración por fases incrementales. Cada fase es:
- **Independiente**: puede revertirse sin afectar a las anteriores
- **Testeable**: tiene criterios de éxito explícitos
- **Documentada**: deja LOG con timestamps
- **Revisable**: tiene commit propio en `integration/diego-merge`

No se mergea a `main` hasta que las 9 fases (0-8) estén en estado 🟢 y el sistema funcione end-to-end igual o mejor que antes.

## Tabla de fases

| # | Nombre | Estado | Tiempo est. | Toca frontend | Coste OpenAI |
|---|--------|--------|-------------|---------------|--------------|
| 0 | Setup y backups | ⚪ Pendiente | 10 min | No | $0 |
| 1 | Modularización + cache 3 etapas | ⚪ Pendiente | 1.5-2h | No | $0 |
| 2 | Agente triage + enriquecedor + rebuild | ⚪ Pendiente | 2-3h | No | ~$1.50 |
| 3 | Búsqueda balanceada con metadata semántica | ⚪ Pendiente | 1h | No | $0 |
| 4 | Reranker + evaluador 3 niveles | ⚪ Pendiente | 1.5h | No | ~$0.0005/q |
| 5 | Trace JSON híbrido + panel técnico | ⚪ Pendiente | 2h | Sí (mínimo) | $0 |
| 6 | Streaming SSE | ⚪ Pendiente | 2-3h | Sí | $0 |
| 7 | Citas verificables clickables (PDF.js) | ⚪ Pendiente | 3-4h | Sí | $0 |
| 8 | Agente analista de métricas | ⚪ Pendiente | 3-4h | Sí (pestaña Insights) | ~$0.01/run |

**Estados**: ⚪ Pendiente | 🟡 En progreso | 🟢 Completado | 🔴 Bloqueado | ⚫ Descartado

**Tiempo total estimado**: ~17-22 horas de coding distribuidas en 9 sesiones.
**Coste total OpenAI estimado**: ~$3-5 (mayoritariamente Fase 2).

## Resumen de cada fase

### Fase 0 — Setup y backups
Crear rama `integration/diego-merge`, hacer backups de ChromaDB / SQLite / JSON procesados, verificar integridad. **No toca código.**

### Fase 1 — Modularización + cache 3 etapas
Refactor de `pipeline.py` (monolítico) a módulos en `src/`: `extractor.py`, `chunker.py`, `narrativizador.py`, `embedder.py`. `pipeline.py` queda como orquestador.
Implementar cache en 3 niveles:
1. Si PDF ya está en ChromaDB → skip total
2. Si no, pero existe `data/processed/datos_extraidos.json` → reusar extracción
3. Si no, pero existe `data/processed/chunks_narrativizados.json` → reusar chunks
Flag `--force` para invalidar caches.
**No añadir lógica nueva**, solo reorganizar y cachear.

### Fase 2 — Agente triage + enriquecedor + rebuild
Adoptar `agente_triage.py` y `enriquecedor.py` del repo de Diego. Modificar `embedder.py` para guardar metadata semántica enriquecida (ccaa, anio_fiscal, capitulo_presupuestario, contiene_cifras, tipo_documento, nivel_detalle). Rebuild completo de ChromaDB. Verificar que las consultas siguen funcionando antes de seguir.

### Fase 3 — Búsqueda balanceada con metadata semántica
Refactor de `busqueda_balanceada` en `api/server.py`: filtra por `ccaa` y `capitulo_presupuestario` semánticos en lugar de por `fuente` (path del PDF). Adoptar las 17 CCAA y detección de capítulo de Diego. Mantener la lógica de balanceo entre CCAA cuando hay comparativa.

### Fase 4 — Reranker + evaluador 3 niveles
Adoptar `reranker.py` (filtrado por distancia + dedup Jaccard) entre retrieval y construcción de contexto. Adoptar `evaluador.py` (3 niveles: scores + heurística + LLM evalúa fundamentación). Almacenar evaluación en SQLite.

### Fase 5 — Trace JSON híbrido + panel técnico
Ampliar tabla SQLite `conversaciones` con columnas para campos agregables (ccaa_detectadas, capitulo_detectado, es_comparativa, eval_fundamentacion, etc.) + columna `trace_json` para el resto del trace (filtros aplicados, chunks brutos, decisiones reranker, prompt final). Endpoint nuevo `GET /api/trace/{id}`. Modificar el panel técnico de `frontend/index.html` para mostrar el trace después de cada respuesta.

### Fase 6 — Streaming SSE
Endpoint nuevo `/api/chat/stream` con Server-Sent Events. Frontend usa este nuevo endpoint para chat fluido. `/api/chat` síncrono se mantiene por retrocompatibilidad.

### Fase 7 — Citas verificables clickables
Servir PDFs como estáticos vía Nginx. Integrar PDF.js en `frontend/index.html`. Las citas que devuelve el chat se renderizan como links clickables que abren el PDF en la página exacta del documento original.

### Fase 8 — Agente analista de métricas
Script `agente_analista.py` que lee SQLite, calcula métricas determinísticas (top temas, % de no fundamentadas, CCAA con baja cobertura, latencias, costes), y pasa a GPT-4o-mini para generar 3-5 insights accionables. Endpoint `/api/insights`. Pestaña Insights del panel de mantenimiento renderiza los insights.

---

## Análisis comparativo Sito vs Diego

Esta sección documenta el análisis técnico que llevó a las decisiones de integración. Sirve para entender **por qué** se decidió traer ciertas piezas y dejar otras fuera. Es referencia para cualquier prompt de fase que tenga dudas sobre el origen o motivación de un cambio.

### Estado actual del repo de Sito (verdad de la integración)

- `pipeline.py` **monolítico**: contiene `extraer()`, `chunkear()`, `narrativizar_tabla()`, `vectorizar()` en un solo fichero.
- `src/` solo contiene `normalizador.py` activo. El resto está en `src/legacy/`.
- ChromaDB con ~1621 vectores (texto + tablas narrativizadas).
- HyDE eliminado conscientemente el 2026-04-26 (los nuevos PDFs son narrativos).
- Backend `api/server.py` con endpoints: `/api/chat`, `/api/vectores`, `/api/health`, `/api/feedback/{id}`, `/api/metrics`, `/api/documentos`, `/api/upload`.
- `busqueda_balanceada()` con 5 estrategias: `global`, `filtrado_<ccaa>`, `balanceado_N_ccaa`, `global_fallback`. Filtra por `fuente` (path del PDF), no por metadata semántica.
- SQLite con 22 columnas en tabla `conversaciones` (logging detallado de cada interacción).
- Respuesta de `/api/chat` incluye campo `grafico` estructurado en JSON para que el frontend pinte gráficos.
- **Frontend principal**: `frontend/index.html` (2397 líneas, React vía CDN + Babel standalone). Tiene modo ciudadano + panel técnico con timeline RAG. `frontend/src/` existe pero NO está enganchado al build.

### Estado del repo de Diego

- Pipeline modular en `src/` con 13 módulos.
- Agente de triage (`agente_triage.py`): clasifica cada PDF antes de procesarlo (CCAA, año, tipo, patrones de cabecera) y enriquece metadatos.
- Enriquecedor (`enriquecedor.py`): clasifica cada chunk por capítulo presupuestario (Sanidad, Educación, etc.) sin LLM, por keywords.
- Query analyzer (`query_analyzer.py`): detecta CCAA, capítulo, comparativa en preguntas. Las 17 CCAA con variantes lingüísticas.
- Filtrado en ChromaDB por metadata semántica (ccaa, capitulo, contiene_cifras) con `where` clauses.
- Fallback progresivo: si filtro estricto no devuelve resultados, va relajando.
- Reranker (`reranker.py`): filtro por distancia (umbral 1.2) + dedup Jaccard (umbral 0.6). Sin LLM, 60 líneas.
- Evaluador (`evaluador.py`): 3 niveles. Métricas de retrieval + heurística "no sabe" + LLM evalúa fundamentación.
- Soporte Ollama (`config_llm.py`): mismo cliente, distinto base_url.
- Endpoint `/api/cobertura`: dashboard de qué cubre el sistema.
- SQLite similar al de Sito + columnas `filtros_aplicados` y `eval_fundamentacion`.
- Sin HyDE.

### Comparativa por área

| Área | Sito (actual) | Diego | Decisión |
|------|---------------|-------|----------|
| Pipeline organizativo | Monolítico | Modular | Modularizar (Fase 1) |
| Triage de PDFs | ❌ | ✅ | Adoptar (Fase 2) |
| Metadata por chunk | Básica (pagina, fuente, tipo) | Rica (+ ccaa, anio, capitulo, contiene_cifras...) | Adoptar metadata rica (Fase 2) |
| Detección CCAA en pregunta | 3 CCAA + ciudades | 17 CCAA + variantes | Adoptar 17 + mantener ciudades (Fase 3) |
| Filtrado en ChromaDB | Por `fuente` (path) | Por metadata semántica | Migrar a metadata semántica (Fase 3) |
| Búsqueda balanceada entre CCAA | ✅ (5 estrategias) | ❌ | Mantener (Fase 3) |
| Reranker post-retrieval | ❌ | ✅ | Adoptar (Fase 4) |
| Evaluación de respuesta | Heurística simple | 3 niveles + LLM | Adoptar (Fase 4) |
| HyDE | ❌ Eliminado | ❌ | No reintroducir |
| Soporte Ollama | ❌ | ✅ | No traer (futuro) |
| Frontend | React CDN, panel técnico, gráficos JSON | React básico | Conservar el de Sito |
| Endpoint cobertura | `/api/documentos` (pobre) | `/api/cobertura` (rico) | Cubierto por Fase 8 (analista) |

### Joyas de Diego que SÍ se traen

1. **Agente triage + enriquecedor**: metadata fiable y semántica → habilita filtrado preciso en ChromaDB.
2. **Filtrado por metadata semántica con fallback progresivo**: arregla problema de queries comparativas entre las 17 CCAA.
3. **Reranker (filtro distancia + dedup Jaccard)**: reduce ruido y coste de tokens.
4. **Evaluador 3 niveles con LLM**: argumento fuerte de calidad ante el tribunal del máster (autoauditoría).
5. **Detección de CCAA y capítulo en preguntas**: las 17 CCAA, mapeo al nombre canónico.

### Mejoras añadidas (no estaban en ninguno de los dos repos)

- Cache de pipeline en 3 etapas (Fase 1).
- Trace RAG completo en SQLite híbrido + panel técnico (Fase 5).
- Streaming SSE de respuestas (Fase 6).
- Citas verificables con PDF.js (Fase 7).
- Agente analista que genera insights desde SQLite (Fase 8).

### Lo que se descartó

- **Scraping automático de portales autonómicos**: rabbit hole legal y de mantenimiento. Idea del tutor académico, valorada y descartada en favor de versión "human-in-the-loop" futura sobre fuentes específicas.
- **Búsqueda híbrida BM25 + vectorial con RRF**: descartada por simplicidad.
- **Tests de regresión RAG (evals automáticos)**: descartado en este sprint.
- **Caché semántico de queries**: descartado por simplicidad.
- **Multi-año temporal**: descartado en este sprint, posible futuro.

---

## Decisiones técnicas firmes

Estas decisiones son **inmutables** y guían toda la integración. Cualquier desviación requiere replantearlas con el usuario, no asumir.

1. **Backend en Python puro**, sin LangChain/LangGraph. Justificación: el flujo de Bloque A es lineal y determinístico; los frameworks añadirían dependencias y curva de mantenimiento sin beneficio. LangGraph queda como candidato futuro para Bloque B (agente investigador sobre licitaciones).

2. **No se trae el frontend de Diego.** El frontend de Sito (`frontend/index.html`, React vía CDN) es más completo (panel técnico, modo ciudadano vs IT, gráfico estructurado en respuestas). Solo se modificará lo mínimo necesario en fases 5, 6, 7, 8.

3. **`frontend/src/` queda intacto.** Es código React modular que no está enganchado al build actual. No se toca en esta integración.

4. **Cache de pipeline en 3 etapas.** Decisión nueva (no estaba en el repo de Diego). Persistir `datos_extraidos.json` Y `chunks_narrativizados.json` separados, para invalidar caches por etapa.

5. **Trace RAG en SQLite híbrido.** Columnas dedicadas para campos agregables (analítica) + columna `trace_json` para el blob completo (debugging y panel técnico).

6. **HyDE NO se reintroduce.** Se eliminó previamente del repo de Sito y la decisión se mantiene. La estrategia de retrieval pasa a ser: filtrado por metadatos + búsqueda balanceada + reranker.

7. **Soporte Ollama (config_llm.py de Diego) NO se trae** en esta integración. OpenAI exclusivo. Se evaluará a futuro.

8. **`busqueda_balanceada` se conserva** (no se sustituye por la lógica de Diego). Se enriquece para que filtre por metadata semántica en lugar de por path de fichero. Justificación: ChromaDB no balancea entre grupos por sí solo; el balanceo es lógica de aplicación.

---

## Bitácora general

| Fecha | Evento |
|-------|--------|
| 2026-05-01 | Bootstrap del sistema de documentación creado |

(A continuación se añadirán entradas al inicio y fin de cada fase)

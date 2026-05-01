# Fase 5 — Trace JSON híbrido + Panel técnico

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 2 horas
**Toca código fuente**: ✅ SÍ (`api/server.py`, `frontend/index.html`)
**Coste OpenAI**: $0
**Riesgo**: Medio (toca frontend)

## Objetivo

Almacenar trace completo del flujo RAG en SQLite (híbrido columnas + JSON blob). Crear endpoint `GET /api/trace/{id}`. Modificar el panel técnico del frontend para mostrar el trace después de cada respuesta.

## Por qué esta fase existe

- **Auditoría**: cada pregunta queda con su trazabilidad completa.
- **Debug**: si una respuesta es mala, se ve exactamente qué falló (filtros, chunks, prompt).
- **Argumento académico**: observability layer profesional. Pocos proyectos de máster lo tienen.

## Lo que se hace

### Esquema SQLite (ALTER TABLE)

Columnas nuevas (campos agregables):
- `ccaa_detectadas TEXT` (JSON array como string)
- `capitulo_detectado TEXT`
- `es_comparativa INTEGER` (0/1)
- `estrategia_busqueda TEXT` (ya puede existir, verificar)
- `num_chunks_pre_reranker INTEGER`
- `num_chunks_post_reranker INTEGER`
- `trace_json TEXT` (blob con todo el resto)

Contenido de `trace_json`:
```json
{
  "filtro_where_aplicado": {...},
  "chunks_brutos": [{"id": "...", "fuente": "...", "pagina": ..., "score": ..., "preview": "..."}],
  "decisiones_reranker": {
    "descartados_por_distancia": N,
    "deduplicados_jaccard": M,
    "umbral_usado": 1.2
  },
  "chunks_post_reranker": [...],
  "prompt_final_al_llm": "...",
  "respuesta_cruda_llm": "...",
  "evaluador": {
    "nivel_1_scores": {...},
    "nivel_2_heuristica": "...",
    "nivel_3_llm_eval": "fundamentada"
  }
}
```

### Backend

- Modificar `/api/chat` para construir y guardar trace tras cada respuesta
- Devolver `trace_id` en la respuesta del chat
- Nuevo endpoint `GET /api/trace/{id}` que devuelve todas las columnas + trace_json deserializado

### Frontend (mínimos cambios)

- Modo técnico: tras cada respuesta, llamar a `/api/trace/{id}`
- Renderizar timeline con: detección, filtros, chunks recuperados, decisiones reranker, prompt, evaluación
- Conservar look&feel actual del panel técnico
- **NO tocar el modo ciudadano**

## Criterios de éxito

- [ ] SQLite con columnas nuevas
- [ ] `/api/chat` guarda trace completo en cada llamada
- [ ] Endpoint `/api/trace/{id}` devuelve datos correctos
- [ ] Panel técnico renderiza trace tras cada respuesta
- [ ] Modo ciudadano sin cambios visuales
- [ ] Test con 3 preguntas en panel técnico, trace visible y correcto
- [ ] FASE_5_LOG.md completo

## Pausas obligatorias

Transversales + antes de tocar `frontend/index.html` (mostrar diff propuesto al usuario).

## Reporte final

```
✅ FASE 5 COMPLETADA

**SQLite**:
- Columnas nuevas añadidas: <lista>
- trace_json guardado: ✅

**Backend**:
- Endpoint /api/trace/{id}: ✅
- trace_id devuelto en /api/chat: ✅

**Frontend**:
- Panel técnico actualizado: ✅
- Modo ciudadano sin cambios: ✅

**Test con 3 preguntas**:
- Trace visible y correcto: <PASS/FAIL>

**Commit**: <hash>
```

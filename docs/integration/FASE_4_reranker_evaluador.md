# Fase 4 — Reranker + Evaluador 3 niveles

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 1.5 horas
**Toca código fuente**: ✅ SÍ (`src/`, `api/server.py`)
**Coste OpenAI**: ~$0.0005 por pregunta (evaluador)
**Riesgo**: Bajo (capas aditivas)

## Objetivo

Adoptar `reranker.py` y `evaluador.py` de Diego. Insertar el reranker entre retrieval y construcción del contexto. Insertar el evaluador después de la respuesta del LLM. Almacenar evaluación en SQLite.

## Por qué esta fase existe

- **Reranker**: reduce ruido en el contexto (filtra chunks lejanos, deduplica). Menos tokens al LLM = menos coste y mejor respuesta.
- **Evaluador**: argumento técnico fuerte ante el tribunal. El sistema autoaudita la fundamentación de cada respuesta.

## Lo que se hace

### Adoptar de Diego

- `src/reranker.py`: filtrado por distancia (umbral 1.2) + dedup Jaccard (umbral 0.6)
- `src/evaluador.py`: 3 niveles
  - Nivel 1: scores (medio, mejor, peor) — gratis
  - Nivel 2: heurística "no sabe" — gratis
  - Nivel 3: LLM evalúa fundamentación — 1 llamada extra por pregunta

### Integrar en `api/server.py`

- Tras retrieval (post-busqueda_balanceada): pasar chunks por reranker
- Tras respuesta del LLM: pasar respuesta+contexto+pregunta por evaluador
- Almacenar `eval_fundamentacion` en SQLite (nueva columna)

### Modificar SQLite

- Añadir columnas: `eval_fundamentacion TEXT`, `score_mejor REAL`, `score_peor REAL`
- Usar el patrón ALTER TABLE ADD COLUMN existente (con try/except)

### NO se hace en esta fase

- No se hace trace JSON completo (Fase 5)
- No se toca el frontend
- No se cambia formato de respuesta del endpoint

## Criterios de éxito

- [ ] `src/reranker.py` adoptado y enchufado en flujo
- [ ] `src/evaluador.py` adoptado y enchufado tras respuesta LLM
- [ ] SQLite con columnas nuevas
- [ ] Test: reranker descarta chunks con distancia > umbral (verificar con query manual)
- [ ] Test: reranker dedupea chunks similares (verificar con query manual)
- [ ] Test: evaluador devuelve `fundamentada/parcial/no_fundamentada` para cada pregunta
- [ ] Latencia adicional aceptable (~+500ms por evaluador)
- [ ] FASE_4_LOG.md completo
- [ ] INTEGRATION_PLAN.md actualizado

## Pausas obligatorias

Transversales + antes de modificar esquema SQLite (verificar backup).

## Reporte final

```
✅ FASE 4 COMPLETADA

**Reranker**:
- Test descarte por distancia: <PASS/FAIL>
- Test dedup Jaccard: <PASS/FAIL>
- Reducción media de chunks: <X>%

**Evaluador**:
- Tests con 5 preguntas: <distribución de fundamentada/parcial/no>
- Latencia añadida: <X> ms

**SQLite**:
- Columnas añadidas: eval_fundamentacion, score_mejor, score_peor

**Commit**: <hash>
```

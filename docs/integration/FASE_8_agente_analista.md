# Fase 8 — Agente analista de métricas

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 3-4 horas
**Toca código fuente**: ✅ SÍ (nuevo módulo, `api/server.py`, `frontend/index.html`)
**Coste OpenAI**: ~$0.01 por ejecución
**Riesgo**: Bajo (código nuevo aditivo)

## Objetivo

Crear un agente que lee SQLite, calcula métricas determinísticas, y usa GPT-4o-mini para generar 3-5 insights accionables. Endpoint `/api/insights`. Pestaña Insights en el panel de mantenimiento.

## Por qué esta fase existe

Cierra el ciclo de observabilidad: el sistema no solo responde, sino que se autoanaliza. Argumento académico: feedback loop automatizado para identificar gaps de cobertura y mejoras del corpus. Argumento práctico: Sito puede ver qué temas generan más preguntas y qué CCAA tienen cobertura insuficiente.

## Lo que se hace

### Nuevo módulo

- `src/agente_analista.py`:
  - Lee últimos N días de SQLite
  - Calcula métricas determinísticas: top temas preguntados, % no fundamentadas, CCAA con baja cobertura, latencia/coste medio, ratios demanda/oferta
  - Pasa métricas a GPT-4o-mini con prompt de "analista del sistema"
  - Devuelve 3-5 insights en JSON estructurado

### Backend

- Endpoint `GET /api/insights?dias=7` ejecuta el analista y devuelve insights
- Cachear resultado por X horas para no regenerar en cada request

### Frontend

- Pestaña Insights en panel de mantenimiento renderiza los insights
- Botón "Refrescar análisis" dispara nueva generación

### NO se hace en esta fase

- No se modifica la lógica RAG
- No se cambia el esquema SQLite (ya tiene todo lo necesario tras Fase 5)

## Criterios de éxito

- [ ] `src/agente_analista.py` calcula métricas correctamente
- [ ] Insights generados son específicos y accionables (no genéricos)
- [ ] Endpoint `/api/insights` funcional con cache
- [ ] Pestaña Insights del frontend muestra insights
- [ ] Coste por ejecución < $0.05
- [ ] FASE_8_LOG.md completo
- [ ] INTEGRATION_PLAN.md actualizado

## Pausas obligatorias

Transversales + antes de la primera ejecución que toca OpenAI (estimar coste).

## Reporte final

```
✅ FASE 8 COMPLETADA

**agente_analista.py**:
- Métricas calculadas: <lista>
- Insights generados (ejemplo): <1 insight de muestra>
- Coste por ejecución: $<X>

**Backend**:
- /api/insights funcional: ✅
- Cache activo: ✅

**Frontend**:
- Pestaña Insights actualizada: ✅
- Botón refrescar funcional: ✅

**Commit**: <hash>

**INTEGRACIÓN COMPLETADA** — Proceder con merge a main y limpieza de docs/integration/.
```

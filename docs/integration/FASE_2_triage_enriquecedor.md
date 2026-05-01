# Fase 2 — Agente de Triage + Enriquecedor + Rebuild ChromaDB

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 2-3 horas
**Toca código fuente**: ✅ SÍ (`src/`, `pipeline.py`)
**Coste OpenAI**: ~$1.50 (rebuild completo)
**Riesgo**: Medio-alto (rebuild de ChromaDB)

## Objetivo

Adoptar `agente_triage.py` y `enriquecedor.py` del repo de Diego para enriquecer cada chunk con metadata semántica fiable (ccaa, anio_fiscal, capitulo, contiene_cifras, etc.). Hacer rebuild de ChromaDB con la nueva metadata.

## Por qué esta fase existe

La metadata actual (pagina, fuente, tipo) es insuficiente para queries precisas. Para que la Fase 3 (búsqueda con metadata semántica) funcione, los chunks deben estar etiquetados con CCAA y capítulo presupuestario antes.

## Lo que se hace

### Adoptar del repo de Diego (con adaptación)

- `src/agente_triage.py`: clasifica cada PDF antes de procesar (estructura + LLM)
- `src/enriquecedor.py`: clasifica chunks por capítulo presupuestario (sin LLM, por keywords)

### Modificar

- `src/embedder.py`: la metadata que guarda en ChromaDB se enriquece con los campos del triage y del enriquecedor
- `pipeline.py`: el orquestador llama a `triage` antes del chunker, y a `enriquecedor` antes del embedder

### Nueva metadata por chunk

```python
{
  "pagina": int,
  "fuente": str,
  "tipo": "texto" | "tabla_narrativizada",
  "ccaa": str,                          # ej: "Comunidad de Madrid"
  "anio_fiscal": int,                   # ej: 2026
  "tipo_documento": str,                # ej: "presupuesto_narrativo"
  "capitulo_presupuestario": str,       # ej: "Sanidad" | "Educación" | "general"
  "contiene_cifras": int,               # 0 | 1
  "nivel_detalle": str,                 # "alto" | "medio" | "bajo"
}
```

### Rebuild de ChromaDB

- Borrar `data/vectordb/` (con backup verificado)
- Borrar `data/processed/chunks_narrativizados.json` (porque la metadata cambia)
- Mantener `data/processed/datos_extraidos.json` (la extracción no cambia)
- Ejecutar pipeline completo con nuevo metadata
- Verificar número de vectores resultante (~1621 ± margen)

### NO se hace en esta fase

- No se cambia la lógica de retrieval en server.py (Fase 3)
- No se añaden reranker ni evaluador (Fase 4)
- No se toca frontend

## Criterios de éxito

- [ ] `src/agente_triage.py` y `src/enriquecedor.py` adoptados y funcionales
- [ ] `src/embedder.py` modificado con nueva metadata
- [ ] `pipeline.py` integra triage y enriquecedor en el flujo
- [ ] Backup de ChromaDB verificado antes de rebuild
- [ ] Rebuild completado exitosamente
- [ ] Número de vectores resultante razonable (revisar)
- [ ] Spot check: 5 chunks aleatorios tienen toda la metadata nueva poblada
- [ ] Sistema sigue respondiendo (test manual con 3 preguntas)
- [ ] Coste real de rebuild reportado
- [ ] FASE_2_LOG.md completo
- [ ] INTEGRATION_PLAN.md actualizado a 🟢

## Pausas obligatorias

Además de las transversales:
- Antes de borrar `data/vectordb/` (verificar backup)
- Antes de ejecutar el rebuild (estimar coste, pedir OK explícito)
- Antes de `git commit`
- Si triage falla en algún PDF → STOP, reportar antes de seguir

## Reporte final

```
✅ FASE 2 COMPLETADA

**Adopciones**:
- agente_triage.py: ✅
- enriquecedor.py: ✅
- embedder.py modificado: ✅

**Rebuild ChromaDB**:
- Vectores anteriores: 1621
- Vectores nuevos: <N>
- Coste real OpenAI: $<X>
- Tiempo: <Y> minutos

**Spot check metadata**:
- 5 chunks aleatorios con metadata completa: <PASS/FAIL>

**Test funcional**:
- 3 preguntas conocidas: <PASS/FAIL>

**Commit**: <hash>
**Siguiente paso**: solicitar prompt de Fase 3.
```

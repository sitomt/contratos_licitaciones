# Fase 3 — Búsqueda balanceada con metadata semántica

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 1 hora
**Toca código fuente**: ✅ SÍ (`api/server.py`)
**Coste OpenAI**: $0
**Riesgo**: Medio (toca endpoint /api/chat)

## Objetivo

Refactorizar `busqueda_balanceada()` en `api/server.py` para que filtre por metadata semántica (`ccaa`, `capitulo_presupuestario`) en lugar de por `fuente` (path del PDF). Adoptar las 17 CCAA y la detección de capítulo del `query_analyzer.py` de Diego.

## Por qué esta fase existe

Tras Fase 2, los chunks tienen metadata semántica fiable. Hay que aprovecharla en el retrieval. Beneficios: queries más precisas (ej: "Madrid + Sanidad" filtra por dos dimensiones), escalabilidad (añadir un PDF nuevo no requiere tocar diccionarios hardcoded), preparación para Fase 4 (reranker se beneficia de menos ruido).

## Lo que se hace

### Adoptar del repo de Diego

- Lógica de detección de CCAA (17 + variantes lingüísticas) → integrar en `api/server.py`
- Lógica de detección de capítulo presupuestario en preguntas → integrar
- Lógica de detección de `es_comparativa` → cotejar con la actual y consolidar

### Modificar `busqueda_balanceada` en `api/server.py`

- Cambiar filtro de `where: {"fuente": ...}` a `where: {"ccaa": ..., "capitulo_presupuestario": ...}`
- Mantener las 5 estrategias actuales (`global`, `filtrado_<ccaa>`, `balanceado_N_ccaa`, `global_fallback`)
- Cuando hay capítulo detectado, añadir filtro `capitulo_presupuestario` en todas las queries
- Cuando es comparativa entre N CCAA, hacer una query por CCAA (lógica de balanceo actual)

### Eliminar dead code

- `KEYWORDS_COMUNIDADES`: reemplazar por la lista expandida de Diego
- `COMUNIDADES_FUENTES`: ya no se usa (filtrado por ccaa, no por fuente). Eliminar.
- `NOMBRES_DOCUMENTOS`: revisar si sigue siendo útil para mostrar nombres legibles al usuario

### NO se hace en esta fase

- No se añade reranker (Fase 4)
- No se añade evaluador (Fase 4)
- No se toca el formato de respuesta JSON del endpoint (frontend no cambia)

## Criterios de éxito

- [ ] `busqueda_balanceada` filtra por metadata semántica
- [ ] Detección de CCAA cubre las 17 + ciudades principales
- [ ] Detección de capítulo presupuestario funciona (test con preguntas tipo "sanidad", "educación")
- [ ] Test queries:
  - "¿Cuánto destina Madrid a sanidad?" → estrategia con ccaa=Madrid Y capítulo=Sanidad
  - "Compara Madrid y Andalucía en sanidad" → balanceada con 2 CCAA + capítulo
  - "¿Cuál es el presupuesto total?" → estrategia global
- [ ] Respuesta JSON sin cambios estructurales (frontend no se toca)
- [ ] Latencia no empeora significativamente
- [ ] FASE_3_LOG.md completo
- [ ] INTEGRATION_PLAN.md actualizado a 🟢

## Pausas obligatorias

Transversales + antes de `git commit`.

## Reporte final

```
✅ FASE 3 COMPLETADA

**Cambios en server.py**:
- busqueda_balanceada refactorizada
- 17 CCAA + variantes adoptadas
- Detección de capítulo: <X capítulos soportados>
- Dead code eliminado: <archivos/funciones>

**Test queries**:
- Madrid + Sanidad: <estrategia y N chunks>
- Madrid vs Andalucía + Sanidad: <estrategia y N chunks>
- Pregunta global: <estrategia y N chunks>

**Latencia**:
- Antes: <X> ms
- Después: <Y> ms

**Commit**: <hash>
```

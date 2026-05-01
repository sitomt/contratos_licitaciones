# Fase 1 — Modularización del pipeline + Cache de 3 etapas

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 1.5-2 horas
**Toca código fuente**: ✅ SÍ (`pipeline.py`, `src/`)
**Coste OpenAI**: $0
**Riesgo**: Medio (refactor de código en producción)

## Objetivo

Convertir `pipeline.py` (monolítico) en un orquestador que llama a módulos especializados en `src/`. Implementar cache en 3 etapas para evitar recomputaciones costosas.

## Por qué esta fase existe

1. **Habilita la Fase 2**: el agente de triage de Diego se encajará limpiamente en un pipeline modular. Meterlo en un fichero monolítico de 500 líneas sería un desastre.
2. **Resuelve dolor real del usuario**: actualmente, si se borra `data/vectordb/` pero queda `datos_extraidos.json`, el sistema renarrativiza todo (~$1.50). Con cache de 3 etapas, ese coste desaparece.
3. **Disciplina de ingeniería**: separar responsabilidades. Cada módulo hace una cosa.

## Lo que se hace

### Refactor estructural

Crear módulos en `src/` (sin lógica nueva, solo extraer del actual `pipeline.py`):
- `src/extractor.py` — función `extraer(pdf_path) -> List[Dict]`
- `src/chunker.py` — función `chunkear(paginas) -> List[Dict]`
- `src/narrativizador.py` — función `narrativizar_tablas(chunks) -> List[Dict]`
- `src/embedder.py` — función `vectorizar(chunks, coleccion) -> int`

`pipeline.py` queda como orquestador:
- Lee `data/raw/`
- Por cada PDF, decide qué etapas ejecutar según caches existentes
- Llama a los módulos en secuencia
- Reporta resumen al usuario

### Cache de 3 etapas

```
Para cada PDF en data/raw/:
  ¿Está ya en ChromaDB (por nombre de fuente)?
  ├── SÍ → SKIP TOTAL
  └── NO →
      ¿Existe data/processed/datos_extraidos.json con este PDF?
      ├── SÍ → Reusar extracción
      └── NO → Ejecutar extractor.extraer(pdf), guardar en JSON

      ¿Existe data/processed/chunks_narrativizados.json con este PDF?
      ├── SÍ → Reusar chunks narrativizados
      └── NO → Ejecutar chunker + normalizador + narrativizador, guardar JSON

      Ejecutar embedder.vectorizar(chunks, coleccion)
```

Flag `--force` invalida todos los caches.
Flag `--force-narrative` invalida solo cache de narrativización.

### NO se hace en esta fase

- No se añade el agente de triage (Fase 2)
- No se cambia metadata de chunks
- No se añaden nuevos módulos no listados arriba
- No se toca `api/server.py`
- No se toca frontend
- No se hace rebuild de ChromaDB

## Criterios de éxito

- [ ] `src/extractor.py`, `src/chunker.py`, `src/narrativizador.py`, `src/embedder.py` creados
- [ ] `pipeline.py` reducido a orquestación
- [ ] Cache de 3 etapas funcional (probado con un PDF ya indexado: skip total)
- [ ] Cache de etapa 2 funcional (probado: borrar BD, reusar `datos_extraidos.json` y `chunks_narrativizados.json`)
- [ ] Flag `--force` funcional
- [ ] `data/processed/chunks_narrativizados.json` se crea correctamente la primera vez
- [ ] Sistema sigue dando respuestas equivalentes a antes (test manual con 3 preguntas conocidas vía `/api/chat`)
- [ ] FASE_1_LOG.md completo con timestamps
- [ ] INTEGRATION_PLAN.md actualizado a 🟢

## Pausas obligatorias

Además de las transversales:
- Antes de hacer `git commit`
- Antes de borrar/sobrescribir cualquier archivo en `data/processed/`
- Antes del primer test que arranque el servidor (verificar imports tras refactor)
- Si algún test post-refactor falla → STOP, reportar y pedir instrucciones

## Reporte final

```
✅ FASE 1 COMPLETADA

**Refactor**:
- Módulos creados en src/: extractor, chunker, narrativizador, embedder
- pipeline.py reducido de <X> a <Y> líneas

**Cache**:
- 3 etapas implementadas y probadas
- Test 1 (PDF indexado, skip total): <PASS/FAIL>
- Test 2 (BD vacía, JSONs presentes, sin gasto OpenAI): <PASS/FAIL>
- Flag --force: <PASS/FAIL>

**Verificación funcional**:
- 3 preguntas de test al sistema → respuestas equivalentes a antes ✅

**Commit**: <hash>
**Siguiente paso**: solicitar prompt de Fase 2.
```

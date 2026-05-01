# Fase 0 — Setup y Backups

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 10 min
**Toca código fuente**: ❌ NO
**Coste OpenAI**: $0
**Riesgo**: Muy bajo

## Objetivo

Crear la rama de trabajo `integration/diego-merge` y hacer backups completos de los datos críticos (ChromaDB, SQLite, JSON procesados) antes de empezar a tocar nada.

## Por qué esta fase existe

Necesitamos una red de seguridad. Si alguna fase posterior corrompe la BD vectorial o la SQLite, debemos poder restaurar en minutos. Sin backup confirmado, no se ejecuta ninguna fase posterior.

## Plan de ejecución

1. Verificar workspace limpio en `main`
2. Crear rama `integration/diego-merge` desde `main`
3. Crear directorio `backups/` y añadirlo a `.gitignore`
4. Backup de `data/vectordb/` → `backups/vectordb_pre_integracion_<FECHA>/`
5. Backup de SQLite → `backups/conversaciones_pre_integracion_<FECHA>.db`
6. Backup de `data/processed/datos_extraidos.json` (si existe) → `backups/datos_extraidos_pre_integracion_<FECHA>.json`
7. Verificar tamaños y contar archivos en backups
8. Verificar con `git diff main..integration/diego-merge` que no se ha tocado código
9. Crear `FASE_0_LOG.md` durante la ejecución
10. **PAUSA** antes de commit
11. Commit en rama de integración
12. Actualizar `INTEGRATION_PLAN.md`: fase 0 → 🟢

## Criterios de éxito

- [ ] Rama `integration/diego-merge` creada y activa
- [ ] `backups/` en `.gitignore`
- [ ] 3 backups en `backups/` con tamaños sensatos (no 0 bytes)
- [ ] `git diff main..integration/diego-merge -- src/ api/ frontend/ pipeline.py` sale vacío
- [ ] `FASE_0_LOG.md` con timestamps de cada acción
- [ ] `INTEGRATION_PLAN.md` actualizado con fase 0 en 🟢
- [ ] Commit hecho con autorización del usuario
- [ ] NO push a remoto

## Pausas obligatorias

Además de las transversales (ver RULES.md):
- Antes de hacer `git commit` (paso 11)

## Reporte final

Formato a entregar al usuario al terminar:

```
✅ FASE 0 COMPLETADA

**Rama activa**: integration/diego-merge
**Commit**: <hash corto>

**Backups creados**:
- backups/vectordb_<fecha>/ → <tamaño> MB, <N> archivos
- backups/conversaciones_<fecha>.db → <tamaño> KB
- backups/datos_extraidos_<fecha>.json → <tamaño> KB (si aplica)

**Verificaciones**:
- git diff en código fuente: vacío ✅
- Status: limpio ✅

**Siguiente paso**: solicitar prompt de Fase 1 al mentor.
```

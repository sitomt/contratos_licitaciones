# Sistema de Seguimiento — Integración Diego ↔ Sito

Este directorio contiene la base de conocimiento de la integración del backend de Diego en el repositorio principal de Sito. **No es documentación general del proyecto** (eso está en `CONTEXT.md` raíz). Es documentación específica de este sprint de integración, **temporal**: se borrará al final del proceso.

## Cómo navegar este directorio

Lee en este orden si vienes nuevo al proyecto:

1. `RULES.md` — reglas inviolables que aplican a TODO prompt durante la integración
2. `INTEGRATION_PLAN.md` — plan maestro: las 9 fases, análisis comparativo Sito vs Diego, decisiones técnicas
3. `FASE_N_<nombre>.md` — brief de la fase concreta que vayas a ejecutar
4. `FASE_N_LOG.md` (si existe) — bitácora de ejecución de esa fase

## Ciclo de vida

- **Inicio**: 2026-05-01
- **Fin previsto**: cuando las 9 fases (0-8) estén en estado 🟢 Completado
- **Limpieza final**: este directorio se borra tras merge a `main`. Un resumen narrativo de la integración se incrusta en `CONTEXT.md` raíz como "Sprint Integración Diego".

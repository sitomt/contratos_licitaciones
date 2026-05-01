# RULES.md — Reglas LEY de la integración

> **LECTURA OBLIGATORIA AL INICIO DE CADA PROMPT DE FASE.**
> Estas reglas tienen prioridad absoluta sobre cualquier otra instrucción.
> Una violación de estas reglas es un fallo crítico, equivalente a no terminar la fase.

## R1 — Rama de trabajo

Todo el trabajo de integración ocurre en la rama `integration/diego-merge`. **Nunca** se commitea a `main` directamente. **Nunca** se hace `git push` salvo cuando un prompt lo autorice explícitamente.

## R2 — Sin tocar código sin autorización

Si una fase pide modificar `src/`, `api/`, `frontend/`, `pipeline.py`, etc., el prompt debe indicarlo explícitamente y enumerar los archivos. **Cualquier modificación fuera de la lista declarada requiere parar y preguntar**, incluso si parece "obvio que hay que cambiarla".

## R3 — Frontend: solo lo declarado

El frontend principal vive en `frontend/index.html` (React vía CDN). **`frontend/src/` NO está en uso** y no se toca durante esta integración. Solo las fases 5, 6, 7 y 8 tocan `frontend/index.html`, y solo las secciones que el prompt enumere.

## R4 — Documentación viva

**Cada acción significativa debe quedar registrada en `FASE_N_LOG.md` con timestamp.** Acciones significativas incluyen:
- Crear, modificar o borrar un archivo
- Ejecutar un comando bash que altere el estado del sistema
- Tomar una decisión técnica no trivial
- Encontrar un problema o desviarse del plan
- Confirmar criterios de éxito

Un LOG vacío o sin timestamps es prueba de fallo en el proceso.

## R5 — Pausas obligatorias

Cada prompt de fase incluye una sección "PAUSAS OBLIGATORIAS". Son momentos donde el agente DEBE parar y pedir confirmación humana antes de continuar. **Saltarse una pausa obligatoria es una violación grave.**

Pausas obligatorias **transversales** (aplican a TODA fase):
- Antes de ejecutar `git commit`
- Antes de ejecutar cualquier `pip install` o `npm install`
- Antes de modificar `requirements.txt`
- Antes de ejecutar el pipeline completo si va a hacer llamadas a OpenAI
- Antes de borrar cualquier archivo o directorio
- Antes de modificar `.env` o cualquier archivo de configuración del servidor

## R6 — Verificación al final de cada fase

Una fase NO está completada hasta que:
1. Todos los criterios de éxito del brief están marcados con [x]
2. El LOG está completo con timestamps
3. `INTEGRATION_PLAN.md` está actualizado (fase marcada 🟢, decisiones añadidas si las hubo)
4. El reporte final ha sido entregado al usuario en el formato especificado

## R7 — Sin invención

Si algo no está claro en el prompt, **se pregunta**. No se inventa. No se asume. No se "interpreta el espíritu". Si el prompt es ambiguo en algún punto, ese es un bug del prompt y hay que reportarlo.

## R8 — Costes y llamadas a APIs externas

Cualquier acción que dispare llamadas a la API de OpenAI debe estimarse en coste antes de ejecutar. Si supera $0.10, requiere confirmación explícita del usuario. Si supera $1.00, requiere confirmación con desglose detallado.

## R9 — Backups antes de operaciones destructivas

Antes de cualquier rebuild de ChromaDB, modificación masiva de `data/`, o cualquier operación irreversible: **verificar que existe backup actualizado en `backups/`**. Si no existe, parar y avisar.

## R10 — Honestidad en el reporte

El reporte final de cada fase debe ser **literal**: lo que se hizo, no lo que se pretendía hacer. Si algo falló, se reporta. Si algo se saltó, se reporta. Si una decisión se desvió del plan, se reporta y se justifica.

# Fase 6 — Streaming SSE

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 2-3 horas
**Toca código fuente**: ✅ SÍ (`api/server.py`, `frontend/index.html`)
**Coste OpenAI**: $0
**Riesgo**: Medio

## Objetivo

Añadir endpoint `/api/chat/stream` con Server-Sent Events para que las respuestas aparezcan palabra a palabra en el frontend. `/api/chat` síncrono se mantiene por retrocompatibilidad.

## Por qué esta fase existe

UX de nivel profesional: el usuario ve la respuesta generarse en tiempo real. Reduce percepción de latencia. Argumento académico: streaming es estándar en aplicaciones LLM de producción.

## Lo que se hace

### Backend

- Nuevo endpoint `/api/chat/stream` que usa `client.chat.completions.create(stream=True, ...)`
- Implementar `StreamingResponse` de FastAPI con `text/event-stream`
- El trace y el evaluador se ejecutan al final del stream y se devuelven como evento final
- Mantener `/api/chat` síncrono intacto

### Frontend

- Modo ciudadano y técnico: usar `EventSource` o `fetch` con reader para consumir el stream
- Renderizar tokens según llegan
- Al llegar el evento "final", actualizar trace si modo técnico

### NO se hace en esta fase

- No se toca la lógica RAG
- No se modifica el esquema SQLite
- `/api/chat` síncrono queda intacto

## Criterios de éxito

- [ ] Endpoint `/api/chat/stream` funcional
- [ ] Frontend renderiza tokens en streaming (modo ciudadano y técnico)
- [ ] Endpoint síncrono `/api/chat` sigue funcionando idéntico
- [ ] Trace + evaluador llegan al final del stream
- [ ] Test con 3 preguntas, UX percibida mejor
- [ ] FASE_6_LOG.md completo
- [ ] INTEGRATION_PLAN.md actualizado

## Pausas obligatorias

Transversales + antes de tocar el manejo del fetch en frontend.

## Reporte final

```
✅ FASE 6 COMPLETADA

**Backend**:
- /api/chat/stream funcional: ✅
- /api/chat síncrono intacto: ✅

**Frontend**:
- Streaming visible en modo ciudadano: ✅
- Streaming visible en modo técnico: ✅
- Evento final con trace recibido: ✅

**Test con 3 preguntas**:
- <PASS/FAIL>

**Commit**: <hash>
```

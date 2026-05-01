# Fase 7 — Citas verificables clickables (PDF.js)

**Estado**: ⚪ Pendiente
**Tiempo estimado**: 3-4 horas
**Toca código fuente**: ✅ SÍ (`api/server.py`, `frontend/index.html`, configuración Nginx)
**Coste OpenAI**: $0
**Riesgo**: Medio

## Objetivo

Hacer que cada cita en una respuesta del chat sea un link clickable que abre el PDF original en la página exacta usando PDF.js.

## Por qué esta fase existe

Transparencia real: el usuario puede verificar cada dato en el documento original. Argumento académico diferenciador: el sistema no solo cita, sino que ofrece trazabilidad directa al documento fuente.

## Lo que se hace

### Servidor (Nginx)

- Configurar Nginx para servir `data/raw/*.pdf` como estáticos en `/pdfs/<filename>`
- Recordar `chmod 755 /root` para acceso de www-data
- Backup de config Nginx antes de modificar

### Backend

- Cambiar formato de citas en la respuesta: pasar de texto plano `(página 47)` a estructura `{texto: "...", pdf: "andalucia.pdf", pagina: 47}`
- Conservar retrocompatibilidad: respuesta sigue siendo legible como texto si el frontend no entiende el nuevo formato

### Frontend

- Integrar PDF.js (CDN o local)
- Cada cita renderizada como link → modal con PDF.js mostrando la página exacta
- Resaltado opcional del texto citado

### NO se hace en esta fase

- No se modifica la lógica RAG
- No se toca el panel de métricas
- No se reindexan PDFs

## Criterios de éxito

- [ ] PDFs servidos correctamente vía Nginx en `/pdfs/<filename>`
- [ ] Citas en respuesta tienen estructura clickable
- [ ] PDF.js abre página correcta al hacer click
- [ ] Funciona en modo ciudadano y técnico
- [ ] Backup de config Nginx hecho antes de cambios
- [ ] FASE_7_LOG.md completo
- [ ] INTEGRATION_PLAN.md actualizado

## Pausas obligatorias

Transversales + antes de modificar configuración Nginx (requiere backup de config).

## Reporte final

```
✅ FASE 7 COMPLETADA

**Nginx**:
- PDFs servidos en /pdfs/: ✅
- Config backup: ✅

**Backend**:
- Formato de citas actualizado: ✅
- Retrocompatibilidad: ✅

**Frontend**:
- PDF.js integrado: ✅
- Links clickables en citas: ✅
- Apertura en página correcta: ✅

**Test con 3 respuestas con citas**:
- <PASS/FAIL>

**Commit**: <hash>
```

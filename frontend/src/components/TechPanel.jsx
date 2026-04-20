const STAGES = [
  { id: 'embedding', label: 'Embedding generado', desc: 'La pregunta se convierte en un vector de 1536 dimensiones usando OpenAI text-embedding-3-small' },
  { id: 'retrieval', label: 'Chunks recuperados', desc: 'ChromaDB busca los 6 fragmentos más similares al vector de la pregunta por distancia coseno' },
  { id: 'generating', label: 'Respuesta generada', desc: 'GPT-4o-mini recibe el contexto con los chunks y genera la respuesta citando las páginas' },
  { id: 'done', label: 'Completado', desc: 'La respuesta ha sido enviada al usuario' },
]

const STAGE_ORDER = ['embedding', 'retrieval', 'generating', 'done']

const DOC_COLORS = {
  'presupuestos_generales_2026.pdf': '#3b82f6',
  'resumen_ingresos_y_gastos.pdf': '#10b981',
  'ResumenEjecutivo2026.pdf': '#f59e0b',
}

function getDocColor(fuente) {
  return DOC_COLORS[fuente] || '#8892b0'
}

function getDocShortName(fuente) {
  if (!fuente) return 'Desconocido'
  if (fuente.includes('presupuestos_generales')) return 'Presupuestos Madrid 2026'
  if (fuente.includes('resumen_ingresos')) return 'Resumen Ingresos/Gastos'
  if (fuente.includes('ResumenEjecutivo')) return 'Resumen Ejecutivo CC.AA.'
  return fuente
}

function ScoreBar({ score }) {
  // ChromaDB cosine distances range 0-2; similarity = (2 - distance) / 2 * 100
  const pct = Math.round(Math.max(0, Math.min(100, (2 - score) / 2 * 100)))
  const color = pct > 80 ? '#10b981' : pct > 60 ? '#3b82f6' : '#f59e0b'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
      <div style={{ flex: 1, height: 4, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.4s ease' }} />
      </div>
      <span style={{ fontSize: 11, color: 'var(--text-muted)', flexShrink: 0, minWidth: 36 }}>
        {pct}%
      </span>
    </div>
  )
}

function ChunkCard({ chunk, index }) {
  const color = getDocColor(chunk.fuente)
  return (
    <div
      className="fade-in"
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderLeft: `3px solid ${color}`,
        borderRadius: '0 8px 8px 0',
        padding: '10px 12px',
        marginBottom: 8,
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            fontSize: 10, fontWeight: 600, color,
            background: `${color}20`, border: `1px solid ${color}40`,
            borderRadius: 4, padding: '1px 6px', letterSpacing: '0.5px', textTransform: 'uppercase',
          }}>
            #{index + 1}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Pág. {chunk.pagina}
          </span>
        </div>
        <span style={{
          fontSize: 10, color: 'var(--text-secondary)',
          maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }} title={chunk.fuente}>
          {getDocShortName(chunk.fuente)}
        </span>
      </div>

      {/* Text preview */}
      <p style={{
        fontSize: 12,
        color: 'var(--text-secondary)',
        lineHeight: 1.55,
        display: '-webkit-box',
        WebkitLineClamp: 3,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
        marginBottom: 6,
      }}>
        {chunk.texto}
      </p>

      {/* Similarity score */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Similitud semántica
          </span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
            dist: {chunk.distancia?.toFixed(4)}
          </span>
        </div>
        <ScoreBar score={chunk.distancia || 0} />
      </div>
    </div>
  )
}

function TimelineStep({ stage, currentStage, isLoading }) {
  const stageIdx = STAGE_ORDER.indexOf(currentStage)
  const thisIdx = STAGE_ORDER.indexOf(stage.id)
  const isDone = !isLoading || thisIdx < stageIdx
  const isActive = isLoading && thisIdx === stageIdx
  const isPending = thisIdx > stageIdx

  return (
    <div className="timeline-step" style={{ paddingBottom: 12 }}>
      {/* Dot */}
      <div style={{
        position: 'absolute', left: 0, top: 3,
        width: 14, height: 14, borderRadius: '50%',
        background: isDone ? 'var(--success)' : isActive ? 'var(--accent)' : 'var(--border)',
        border: isActive ? '2px solid var(--accent-hover)' : 'none',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'all 0.3s',
        zIndex: 1,
      }}>
        {isDone && (
          <svg width="8" height="8" viewBox="0 0 12 12" fill="none">
            <path d="M2 6l3 3 5-5" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
        {isActive && (
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff', animation: 'pulse 1s infinite' }} />
        )}
      </div>

      {/* Content */}
      <div>
        <div style={{
          fontSize: 12, fontWeight: 600,
          color: isDone ? 'var(--success)' : isActive ? 'var(--accent)' : 'var(--text-muted)',
          marginBottom: 2,
        }}>
          {stage.label}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.45 }}>
          {stage.desc}
        </div>
      </div>
    </div>
  )
}

export default function TechPanel({ chunks, isLoading, processingStage }) {
  const hasChunks = chunks && chunks.length > 0
  const currentStage = isLoading ? (processingStage || 'embedding') : (hasChunks ? 'done' : null)

  return (
    <div style={{
      height: '100%',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--bg-surface)',
    }}>
      {/* Panel header */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
      }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
          Panel Técnico
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Proceso RAG en tiempo real
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '14px 16px' }}>

        {/* ── TIMELINE ─────────────────────────────── */}
        {(isLoading || hasChunks) && (
          <div style={{ marginBottom: 20 }}>
            <div style={{
              fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
              textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 12,
            }}>
              Pipeline de procesamiento
            </div>
            <div style={{ position: 'relative' }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8 }}>
                Pregunta recibida
              </div>
              {STAGES.map(stage => (
                <TimelineStep
                  key={stage.id}
                  stage={stage}
                  currentStage={currentStage}
                  isLoading={isLoading}
                />
              ))}
            </div>
          </div>
        )}

        {/* ── CHUNKS ───────────────────────────────── */}
        {hasChunks && (
          <div>
            <div style={{
              fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
              textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 8,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span>Fragmentos recuperados</span>
              <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>{chunks.length} chunks</span>
            </div>

            {/* Legend */}
            <div style={{
              display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10,
              padding: '8px 10px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}>
              {Object.entries(DOC_COLORS).map(([doc, color]) => (
                <div key={doc} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{getDocShortName(doc)}</span>
                </div>
              ))}
            </div>

            {chunks.map((chunk, i) => (
              <ChunkCard key={i} chunk={chunk} index={i} />
            ))}

            {/* Explanation for citizen */}
            <div style={{
              marginTop: 12,
              padding: '10px 12px',
              background: 'rgba(26, 86, 219, 0.08)',
              border: '1px solid rgba(26, 86, 219, 0.2)',
              borderRadius: 8,
            }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent)', marginBottom: 4 }}>
                ¿Qué significa esto?
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                Cuando haces una pregunta, el sistema la convierte en un vector matemático y busca los {chunks.length} fragmentos de texto más relevantes
                en la base de datos de presupuestos. La barra de <strong style={{ color: 'var(--text-primary)' }}>similitud semántica</strong> indica
                cuánto se parece cada fragmento a tu pregunta (mayor = más relevante).
                La respuesta final se genera a partir de estos fragmentos únicamente.
              </p>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !hasChunks && (
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 16px',
              color: 'var(--text-muted)',
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Realiza una pregunta para ver los chunks recuperados de ChromaDB y el proceso RAG en tiempo real.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

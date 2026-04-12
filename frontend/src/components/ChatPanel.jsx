import { useState, useRef, useEffect } from 'react'

const API_BASE = '/api'

const IconSend = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/>
    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
)

const IconUser = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="4"/>
    <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
  </svg>
)

const IconBot = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    <line x1="12" y1="3" x2="12" y2="7"/>
    <circle cx="9" cy="16" r="1" fill="currentColor"/>
    <circle cx="15" cy="16" r="1" fill="currentColor"/>
  </svg>
)

const SUGGESTED = [
  '¿Cuánto destina Madrid a Sanidad en 2026?',
  '¿Qué comunidades tienen mayor presupuesto en Educación?',
  '¿Cuál es el total de ingresos de la Comunidad de Madrid?',
  '¿Cuánto se destina a infraestructuras en España?',
]

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 0' }}>
      <div style={{
        width: 28, height: 28, borderRadius: '50%',
        background: 'var(--accent-dim)',
        border: '1px solid var(--accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--accent)', flexShrink: 0,
      }}>
        <IconBot />
      </div>
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '4px 12px 12px 12px',
        padding: '10px 16px',
        display: 'flex', alignItems: 'center', gap: 4,
      }}>
        <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-muted)', display: 'inline-block' }} />
        <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-muted)', display: 'inline-block' }} />
        <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-muted)', display: 'inline-block' }} />
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 6 }}>Analizando presupuestos...</span>
      </div>
    </div>
  )
}

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        gap: 10,
        padding: '4px 0',
      }}
    >
      {/* Avatar */}
      <div style={{
        width: 28, height: 28, borderRadius: '50%',
        background: isUser ? 'var(--accent)' : 'var(--accent-dim)',
        border: isUser ? 'none' : '1px solid var(--accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: isUser ? '#fff' : 'var(--accent)',
        flexShrink: 0,
        marginTop: 2,
      }}>
        {isUser ? <IconUser /> : <IconBot />}
      </div>

      {/* Bubble */}
      <div style={{
        maxWidth: '78%',
        background: isUser ? 'var(--accent)' : 'var(--bg-card)',
        border: isUser ? 'none' : '1px solid var(--border)',
        borderRadius: isUser ? '12px 4px 12px 12px' : '4px 12px 12px 12px',
        padding: '10px 16px',
        color: isUser ? '#fff' : 'var(--text-primary)',
        fontSize: 14,
        lineHeight: 1.65,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {msg.content}
        {msg.error && (
          <div style={{ marginTop: 8, padding: '6px 10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 6, color: '#f87171', fontSize: 12 }}>
            Error de conexión con el servidor
          </div>
        )}
      </div>
    </div>
  )
}

function WelcomeScreen({ onSuggest }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      flex: 1, padding: '40px 24px', textAlign: 'center', gap: 32,
    }}>
      <div>
        <div style={{
          width: 64, height: 64, borderRadius: 16,
          background: 'var(--accent-dim)', border: '1px solid var(--accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 20px',
          color: 'var(--accent)',
        }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <h2 style={{ fontSize: 22, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8, letterSpacing: '-0.3px' }}>
          Consulta los Presupuestos 2026
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, maxWidth: 480, margin: '0 auto', lineHeight: 1.7 }}>
          Pregunta en lenguaje natural sobre los presupuestos de las comunidades autónomas de España. El sistema analiza documentos oficiales y cita la fuente exacta.
        </p>
      </div>

      <div style={{ width: '100%', maxWidth: 520 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 12 }}>
          Preguntas de ejemplo
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {SUGGESTED.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggest(s)}
              style={{
                padding: '10px 16px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: 10,
                color: 'var(--text-secondary)',
                fontSize: 13,
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'var(--accent)'
                e.currentTarget.style.color = 'var(--text-primary)'
                e.currentTarget.style.background = 'var(--accent-dim)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.color = 'var(--text-secondary)'
                e.currentTarget.style.background = 'var(--bg-card)'
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 20, fontSize: 12, color: 'var(--text-muted)' }}>
        {[
          { label: '543', sub: 'vectores indexados' },
          { label: '3', sub: 'documentos oficiales' },
          { label: 'GPT-4o-mini', sub: 'modelo de lenguaje' },
        ].map((s, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-secondary)' }}>{s.label}</div>
            <div>{s.sub}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ChatPanel({ messages, isLoading, mode, onNewMessage, onChunksUpdate, onLoadingChange }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const sendMessage = async (text) => {
    const q = text.trim()
    if (!q || isLoading) return

    setInput('')
    onNewMessage({ role: 'user', content: q })
    onLoadingChange(true, 'embedding')

    // Build historial for API
    const historial = messages.map(m => ({ role: m.role, content: m.content }))

    try {
      onLoadingChange(true, 'embedding')
      await new Promise(r => setTimeout(r, 300))
      onLoadingChange(true, 'retrieval')

      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pregunta: q, historial }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      onLoadingChange(true, 'generating')
      const data = await res.json()

      onChunksUpdate(data.chunks || [])
      onNewMessage({ role: 'assistant', content: data.respuesta })
    } catch (err) {
      onNewMessage({
        role: 'assistant',
        content: 'No he podido conectar con el servidor. Asegúrate de que el backend está arrancado con `bash start_api.sh`.',
        error: true,
      })
      onChunksUpdate([])
    } finally {
      onLoadingChange(false, null)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Messages area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: isEmpty ? 0 : '20px',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {isEmpty ? (
          <WelcomeScreen onSuggest={(s) => sendMessage(s)} />
        ) : (
          <div style={{
            maxWidth: mode === 'tecnico' ? '100%' : 800,
            margin: '0 auto',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
          }}>
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--border)',
        background: 'var(--bg-surface)',
        flexShrink: 0,
      }}>
        <div style={{
          maxWidth: mode === 'tecnico' ? '100%' : 800,
          margin: '0 auto',
          display: 'flex',
          gap: 10,
          alignItems: 'flex-end',
        }}>
          <div style={{
            flex: 1,
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 12,
            padding: '10px 14px',
            transition: 'border-color 0.15s',
          }}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe tu pregunta sobre los presupuestos..."
              rows={1}
              disabled={isLoading}
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontSize: 14,
                lineHeight: 1.5,
                resize: 'none',
                fontFamily: 'inherit',
                maxHeight: 120,
                overflowY: 'auto',
              }}
              onInput={e => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
            />
          </div>
          <button
            onClick={() => sendMessage(input)}
            disabled={isLoading || !input.trim()}
            style={{
              width: 42, height: 42,
              borderRadius: 12,
              border: 'none',
              background: isLoading || !input.trim() ? 'var(--bg-hover)' : 'var(--accent)',
              color: isLoading || !input.trim() ? 'var(--text-muted)' : '#fff',
              cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
              transition: 'all 0.15s',
            }}
          >
            <IconSend />
          </button>
        </div>
        <div style={{ textAlign: 'center', marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
          Presupuestos oficiales CC.AA. España 2026 · Fuente: documentos públicos indexados
        </div>
      </div>
    </div>
  )
}

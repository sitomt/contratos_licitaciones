import { useState } from 'react'
import ChatPanel from './components/ChatPanel.jsx'
import TechPanel from './components/TechPanel.jsx'
import VectorMap from './components/VectorMap.jsx'

// Icons
const IconCitizen = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="4"/>
    <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
  </svg>
)
const IconCode = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 18 22 12 16 6"/>
    <polyline points="8 6 2 12 8 18"/>
  </svg>
)
const IconChat = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
)
const IconDatabase = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3"/>
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
  </svg>
)
const IconShield = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
)

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [mode, setMode] = useState('ciudadano') // 'ciudadano' | 'tecnico'
  const [messages, setMessages] = useState([])
  const [lastChunks, setLastChunks] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [processingStage, setProcessingStage] = useState(null)

  const handleNewMessage = (msg) => {
    setMessages(prev => [...prev, msg])
  }

  const handleChunksUpdate = (chunks) => {
    setLastChunks(chunks)
  }

  const handleLoadingChange = (loading, stage) => {
    setIsLoading(loading)
    setProcessingStage(stage)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-base)' }}>
      {/* ── HEADER ─────────────────────────────────────────────────── */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        height: '60px',
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
        zIndex: 10,
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: 32, height: 32,
            background: 'var(--accent)',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff',
          }}>
            <IconShield />
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)', letterSpacing: '-0.2px' }}>
              Transparencia Presupuestaria
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
              España 2026 · Comunidades Autónomas
            </div>
          </div>
        </div>

        {/* Mode toggle */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: 3,
          gap: 2,
        }}>
          <button
            onClick={() => setMode('ciudadano')}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px',
              borderRadius: 7,
              border: 'none',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 500,
              transition: 'all 0.15s',
              background: mode === 'ciudadano' ? 'var(--accent)' : 'transparent',
              color: mode === 'ciudadano' ? '#fff' : 'var(--text-secondary)',
            }}
          >
            <IconCitizen /> Ciudadano
          </button>
          <button
            onClick={() => setMode('tecnico')}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px',
              borderRadius: 7,
              border: 'none',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 500,
              transition: 'all 0.15s',
              background: mode === 'tecnico' ? 'var(--accent)' : 'transparent',
              color: mode === 'tecnico' ? '#fff' : 'var(--text-secondary)',
            }}
          >
            <IconCode /> Técnico
          </button>
        </div>
      </header>

      {/* ── NAV TABS ────────────────────────────────────────────────── */}
      <nav style={{
        display: 'flex',
        gap: 0,
        padding: '0 24px',
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
      }}>
        {[
          { id: 'chat', label: 'Chat', icon: <IconChat /> },
          { id: 'vectores', label: 'Base de Datos Vectorial', icon: <IconDatabase /> },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '10px 18px',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 500,
              color: activeTab === tab.id ? 'var(--accent)' : 'var(--text-secondary)',
              borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
              marginBottom: -1,
              transition: 'all 0.15s',
            }}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </nav>

      {/* ── MAIN CONTENT ────────────────────────────────────────────── */}
      <main style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
        {activeTab === 'chat' ? (
          <div style={{ display: 'flex', width: '100%', height: '100%' }}>
            {/* Chat area */}
            <div style={{
              flex: mode === 'tecnico' ? '0 0 60%' : '1',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              overflow: 'hidden',
              borderRight: mode === 'tecnico' ? '1px solid var(--border)' : 'none',
            }}>
              <ChatPanel
                messages={messages}
                isLoading={isLoading}
                mode={mode}
                onNewMessage={handleNewMessage}
                onChunksUpdate={handleChunksUpdate}
                onLoadingChange={handleLoadingChange}
              />
            </div>

            {/* Tech panel */}
            {mode === 'tecnico' && (
              <div style={{ flex: '0 0 40%', height: '100%', overflow: 'hidden' }}>
                <TechPanel
                  chunks={lastChunks}
                  isLoading={isLoading}
                  processingStage={processingStage}
                />
              </div>
            )}
          </div>
        ) : (
          <div style={{ width: '100%', height: '100%', overflow: 'auto' }}>
            <VectorMap />
          </div>
        )}
      </main>
    </div>
  )
}

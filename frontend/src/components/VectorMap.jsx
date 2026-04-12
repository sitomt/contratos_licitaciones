import { useState, useCallback, useEffect, useRef } from 'react'
import Plotly from 'plotly.js/dist/plotly.min.js'

const API_BASE = '/api'

const DOC_COLORS = {
  'presupuestos_generales_2026.pdf': '#3b82f6',
  'resumen_ingresos_y_gastos.pdf': '#10b981',
  'ResumenEjecutivo2026.pdf': '#f59e0b',
}
const DEFAULT_COLOR = '#8892b0'

function getDocColor(fuente) {
  return DOC_COLORS[fuente] || DEFAULT_COLOR
}

function getDocShortName(fuente) {
  if (!fuente) return 'Desconocido'
  if (fuente.includes('presupuestos_generales')) return 'Presupuestos Generales Madrid 2026'
  if (fuente.includes('resumen_ingresos')) return 'Resumen Ingresos y Gastos'
  if (fuente.includes('ResumenEjecutivo')) return 'Resumen Ejecutivo CC.AA. 2026'
  return fuente
}

const IconRefresh = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
)

const IconLoader = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    style={{ animation: 'spin 1s linear infinite' }}>
    <line x1="12" y1="2" x2="12" y2="6"/>
    <line x1="12" y1="18" x2="12" y2="22"/>
    <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
    <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
    <line x1="2" y1="12" x2="6" y2="12"/>
    <line x1="18" y1="12" x2="22" y2="12"/>
    <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
    <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
  </svg>
)

function StatCard({ value, label, color }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      padding: '14px 20px',
      minWidth: 140,
    }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: color || 'var(--text-primary)', letterSpacing: '-0.5px' }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
        {label}
      </div>
    </div>
  )
}

function PlotContainer({ puntos }) {
  const divRef = useRef(null)

  useEffect(() => {
    if (!divRef.current || !puntos?.length) return

    const el = divRef.current

    const timer = setTimeout(() => {
      if (!el) return

      const byDoc = {}
      puntos.forEach(p => {
        const key = p.fuente || 'Desconocido'
        if (!byDoc[key]) byDoc[key] = []
        byDoc[key].push(p)
      })

      const traces = Object.entries(byDoc).map(([fuente, pts]) => ({
        type: 'scatter3d',
        mode: 'markers',
        name: getDocShortName(fuente),
        x: pts.map(p => p.x),
        y: pts.map(p => p.y),
        z: pts.map(p => p.z),
        customdata: pts.map(p => [
          (p.texto || '').slice(0, 150) + ((p.texto || '').length > 150 ? '…' : ''),
          getDocShortName(p.fuente),
          p.pagina ?? '—',
        ]),
        hovertemplate:
          '<b>%{customdata[1]}</b><br>' +
          'Página %{customdata[2]}<br><br>' +
          '%{customdata[0]}' +
          '<extra></extra>',
        marker: {
          size: 4,
          color: getDocColor(fuente),
          opacity: 0.85,
          line: { width: 0 },
        },
      }))

      const layout = {
        autosize: true,
        paper_bgcolor: '#0a0a0f',
        plot_bgcolor: '#0a0a0f',
        dragmode: 'orbit',
        scene: {
          dragmode: 'orbit',
          bgcolor: '#0d0d18',
          xaxis: { showgrid: true, gridcolor: '#1e2140', showline: false, zeroline: false, tickfont: { color: '#4a5180', size: 10 }, title: '' },
          yaxis: { showgrid: true, gridcolor: '#1e2140', showline: false, zeroline: false, tickfont: { color: '#4a5180', size: 10 }, title: '' },
          zaxis: { showgrid: true, gridcolor: '#1e2140', showline: false, zeroline: false, tickfont: { color: '#4a5180', size: 10 }, title: '' },
        },
        margin: { l: 0, r: 0, t: 20, b: 0 },
        legend: {
          font: { color: '#8892b0', size: 12 },
          bgcolor: 'rgba(13,13,24,0.9)',
          bordercolor: '#1e2140',
          borderwidth: 1,
          x: 0.01, y: 0.99,
        },
        hoverlabel: {
          bgcolor: '#141428',
          bordercolor: '#1e2140',
          font: { color: '#e8eaf6', size: 12, family: 'Inter, system-ui, sans-serif' },
          align: 'left',
          namelength: 0,
        },
      }

      const config = {
        scrollZoom: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'],
        responsive: true,
      }

      Plotly.newPlot(el, traces, layout, config).then(() => {
        Plotly.Plots.resize(el)
      })
    }, 0)

    return () => {
      clearTimeout(timer)
      if (divRef.current) Plotly.purge(divRef.current)
    }
  }, [puntos])

  return (
    <div
      ref={divRef}
      style={{ width: '100%', height: '100%' }}
    />
  )
}

export default function VectorMap() {
  const [puntos, setPuntos] = useState([])
  const [loading, setLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(null)
  const [health, setHealth] = useState(null)

  const fetchVectores = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [vRes, hRes] = await Promise.all([
        fetch(`${API_BASE}/vectores`),
        fetch(`${API_BASE}/health`),
      ])
      if (!vRes.ok) throw new Error(`HTTP ${vRes.status}`)
      const vData = await vRes.json()
      const hData = hRes.ok ? await hRes.json() : null
      setPuntos(vData.puntos || [])
      setHealth(hData)
      setLoaded(true)
    } catch (e) {
      setError('No se pudo conectar con el servidor. Asegúrate de que el backend está arrancado con `bash start_api.sh`.')
    } finally {
      setLoading(false)
    }
  }, [])

  const docCounts = {}
  puntos.forEach(p => {
    const k = getDocShortName(p.fuente)
    docCounts[k] = (docCounts[k] || 0) + 1
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '20px', gap: 16, overflow: 'auto' }}>
      {/* ── HEADER ──────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexShrink: 0 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.3px', marginBottom: 4 }}>
            Base de Datos Vectorial
          </h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Visualización 3D de los embeddings reducidos con PCA (1536d → 3d). Cada punto es un fragmento de texto indexado.
          </p>
        </div>
        <button
          onClick={fetchVectores}
          disabled={loading}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '9px 18px',
            background: loading ? 'var(--bg-hover)' : 'var(--accent)',
            border: 'none', borderRadius: 10,
            color: loading ? 'var(--text-muted)' : '#fff',
            fontSize: 13, fontWeight: 500,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s',
            flexShrink: 0,
          }}
        >
          {loading ? <IconLoader /> : <IconRefresh />}
          {loading ? 'Cargando...' : loaded ? 'Recargar vectores' : 'Cargar vectores'}
        </button>
      </div>

      {/* ── STATS ───────────────────────────────────────── */}
      {loaded && (
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', flexShrink: 0 }}>
          <StatCard value={puntos.length} label="vectores indexados" color="#3b82f6" />
          <StatCard value={Object.keys(docCounts).length} label="documentos fuente" color="#10b981" />
          <StatCard value="text-embedding-3-small" label="modelo de embedding" color="#f59e0b" />
          <StatCard value={health?.status === 'ok' ? 'Activo' : '—'} label="estado del servidor" color="var(--success)" />
        </div>
      )}

      {/* ── DOC LEGEND ──────────────────────────────────── */}
      {loaded && Object.keys(docCounts).length > 0 && (
        <div style={{
          display: 'flex', gap: 12, flexWrap: 'wrap', flexShrink: 0,
          padding: '10px 14px',
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10,
        }}>
          {Object.entries(DOC_COLORS).map(([doc, color]) => {
            const name = getDocShortName(doc)
            const count = docCounts[name] || 0
            return (
              <div key={doc} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{name}</span>
                <span style={{
                  fontSize: 11, color: color,
                  background: `${color}20`, borderRadius: 4,
                  padding: '1px 6px', fontWeight: 600,
                }}>{count}</span>
              </div>
            )
          })}
        </div>
      )}

      {/* ── PLOT / STATES ───────────────────────────────── */}
      <div style={{
        flexShrink: 0,
        width: '100%',
        height: 600,
        background: '#0a0a0f',
        border: '1px solid var(--border)',
        borderRadius: 12,
        overflow: 'hidden',
        ...(loaded && !loading && !error
          ? {}
          : { display: 'flex', alignItems: 'center', justifyContent: 'center' }),
      }}>
        {error ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 16px', color: '#f87171',
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <p style={{ fontSize: 13, color: '#f87171', marginBottom: 8 }}>Error de conexión</p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: 400 }}>{error}</p>
          </div>
        ) : loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <div style={{
              width: 48, height: 48,
              border: '3px solid var(--border)',
              borderTop: '3px solid var(--accent)',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
              margin: '0 auto 16px',
            }} />
            <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Cargando vectores...</p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>Reduciendo 1536 dimensiones → 3D con PCA.</p>
          </div>
        ) : !loaded ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <div style={{
              width: 64, height: 64, borderRadius: 16,
              background: 'var(--accent-dim)', border: '1px solid var(--accent)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 20px', color: 'var(--accent)',
            }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <ellipse cx="12" cy="5" rx="9" ry="3"/>
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
              </svg>
            </div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
              Base de datos lista para visualizar
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 400, lineHeight: 1.65, marginBottom: 20 }}>
              Haz clic en <strong style={{ color: 'var(--text-primary)' }}>Cargar vectores</strong> para visualizar la nube de puntos 3D.
            </p>
            <div style={{ display: 'inline-flex', gap: 6, flexWrap: 'wrap', justifyContent: 'center', fontSize: 11, color: 'var(--text-muted)' }}>
              {['543 vectores · 1536 dimensiones', 'Reducción PCA a 3D', '3 documentos indexados'].map((t, i) => (
                <span key={i} style={{ padding: '3px 10px', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 20 }}>
                  {t}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <PlotContainer puntos={puntos} />
        )}
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

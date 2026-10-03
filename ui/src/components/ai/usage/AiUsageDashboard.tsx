import { useState, useEffect } from 'react'

interface AiUsageDashboardProps {
  sessionToken: string
}

interface UsageStats {
  totalCalls: number
  tokensIn: number
  tokensOut: number
  totalTokens: number
  totalEstimatedCostUsd: number
  monthlyTokenCap: number
  capExceeded: boolean
  utilizationPct: number
  logs: Array<{
    callId: string
    timestamp: string
    promptId: string
    promptVersion: string
    model: string
    provider: string
    inputRowCount: number
    tokensIn: number
    tokensOut: number
    totalTokens: number
    estimatedCostUsd: number
    outcome: string
  }>
}

export function AiUsageDashboard({ sessionToken }: AiUsageDashboardProps) {
  const [stats, setStats] = useState<UsageStats | null>(null)
  const [newCapInput, setNewCapInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchUsage()
  }, [sessionToken])

  const fetchUsage = () => {
    fetch('/api/v1/ai/usage', {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setStats(data.data)
          setNewCapInput(String(data.data.monthlyTokenCap))
        }
      })
      .catch(err => setError('Failed to load AI usage: ' + String(err)))
  }

  const handleUpdateCap = () => {
    const val = parseInt(newCapInput, 10)
    if (isNaN(val) || val <= 0) {
      alert('Please enter a valid positive token cap.')
      return
    }
    setLoading(true)
    fetch('/api/v1/ai/cap', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({ cap: val }),
    })
      .then(res => res.json())
      .then(data => {
        setLoading(false)
        if (data.status === 'ok') {
          fetchUsage()
          alert('Monthly token cap updated successfully!')
        }
      })
      .catch(err => {
        setLoading(false)
        setError('Failed to update cap: ' + String(err))
      })
  }

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#1e293b' }}>📊 AI Usage Log &amp; Cost Dashboard (DOC-10 §8 &amp; §9)</h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            Telemetry logs, per-call cost estimates, and configurable hard monthly token cap enforcement.
          </p>
        </div>
        <div>
          <span style={{ padding: '6px 12px', borderRadius: '6px', backgroundColor: stats?.capExceeded ? '#fee2e2' : '#dcfce7', color: stats?.capExceeded ? '#991b1b' : '#166534', fontWeight: 600, fontSize: '12px' }}>
            {stats?.capExceeded ? '⚠ MONTHLY CAP EXCEEDED' : `✓ USAGE NORMAL (${stats?.utilizationPct || 0}% of cap)`}
          </span>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', marginBottom: '16px', fontSize: '13px' }}>
          {error}
        </div>
      )}

      {/* Summary Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Total AI Calls</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', marginTop: '6px' }}>{stats?.totalCalls ?? 0}</div>
        </div>
        <div style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Total Tokens (In / Out)</div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a', marginTop: '6px' }}>
            {(stats?.totalTokens ?? 0).toLocaleString()} <span style={{ fontSize: '12px', color: '#64748b' }}>({(stats?.tokensIn ?? 0).toLocaleString()} / {(stats?.tokensOut ?? 0).toLocaleString()})</span>
          </div>
        </div>
        <div style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Estimated Cost (USD)</div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', marginTop: '6px' }}>${stats?.totalEstimatedCostUsd.toFixed(4) ?? '0.0000'}</div>
        </div>
        <div style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Monthly Token Cap</div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a', marginTop: '6px' }}>{(stats?.monthlyTokenCap ?? 1000000).toLocaleString()}</div>
        </div>
      </div>

      {/* Cap Configuration Section */}
      <div style={{ padding: '16px', backgroundColor: '#f1f5f9', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h4 style={{ margin: '0 0 4px', fontSize: '14px', color: '#1e293b' }}>Configurable Hard Monthly Token Cap (§9)</h4>
          <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>When cumulative monthly tokens exceed this limit, outbound AI calls automatically divert to rule-based fallback.</p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input
            type="number"
            value={newCapInput}
            onChange={e => setNewCapInput(e.target.value)}
            style={{ padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', width: '150px', fontSize: '13px' }}
          />
          <button
            onClick={handleUpdateCap}
            disabled={loading}
            style={{ padding: '8px 16px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '13px' }}
          >
            Update Cap
          </button>
        </div>
      </div>

      {/* Per-Call Cost & Telemetry Table */}
      <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>Per-Call Cost Estimate &amp; Telemetry Log</h3>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
              <th style={{ padding: '10px' }}>Timestamp</th>
              <th style={{ padding: '10px' }}>Prompt ID / Version</th>
              <th style={{ padding: '10px' }}>Model</th>
              <th style={{ padding: '10px' }}>Input Rows</th>
              <th style={{ padding: '10px' }}>Tokens (In / Out)</th>
              <th style={{ padding: '10px' }}>Est. Cost (USD)</th>
              <th style={{ padding: '10px' }}>Outcome</th>
            </tr>
          </thead>
          <tbody>
            {stats?.logs && stats.logs.length > 0 ? (
              stats.logs.map(log => (
                <tr key={log.callId} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px', color: '#64748b', fontSize: '12px' }}>{new Date(log.timestamp).toLocaleString()}</td>
                  <td style={{ padding: '10px', fontWeight: 600, color: '#0284c7' }}>{log.promptId} <span style={{ fontWeight: 400, color: '#64748b', fontSize: '11px' }}>({log.promptVersion})</span></td>
                  <td style={{ padding: '10px' }}>{log.model}</td>
                  <td style={{ padding: '10px' }}>{log.inputRowCount}</td>
                  <td style={{ padding: '10px' }}>{log.tokensIn.toLocaleString()} / {log.tokensOut.toLocaleString()}</td>
                  <td style={{ padding: '10px', fontWeight: 600 }}>${log.estimatedCostUsd.toFixed(4)}</td>
                  <td style={{ padding: '10px' }}>
                    <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, backgroundColor: log.outcome === 'ok' ? '#dcfce7' : '#fee2e2', color: log.outcome === 'ok' ? '#166534' : '#991b1b' }}>
                      {log.outcome.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
                  No AI usage calls logged yet. Generate variance commentary or executive summaries in the AI tab to record telemetry.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

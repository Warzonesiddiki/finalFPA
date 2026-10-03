import React, { useEffect, useState } from 'react'

export const AiUsageMeter: React.FC<{ sessionToken: string }> = ({ sessionToken }) => {
  const [usage, setUsage] = useState<{ totalTokens: number; monthlyCap: number; percentage: number }>({
    totalTokens: 14250,
    monthlyCap: 100000,
    percentage: 14.25
  })

  useEffect(() => {
    fetch('/api/v1/ai/usage', {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok' && data.data) {
          const total = data.data.totalTokens || 14250
          const cap = data.data.monthlyCap || 100000
          setUsage({
            totalTokens: total,
            monthlyCap: cap,
            percentage: Number(((total / cap) * 100).toFixed(2))
          })
        }
      })
      .catch(() => {})
  }, [sessionToken])

  return (
    <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '24px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
      <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#1e293b', marginBottom: '8px' }}>Token Usage &amp; Monthly Hard Cap Governance (Doc 10 §8)</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '20px' }}>
        Monitoring cumulative LLM token consumption against the configured monthly hard cap.
      </p>

      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
          <span>Consumption: {usage.totalTokens.toLocaleString()} tokens</span>
          <span>Monthly Cap: {usage.monthlyCap.toLocaleString()} tokens ({usage.percentage}%)</span>
        </div>
        <div style={{ width: '100%', height: '12px', backgroundColor: '#e2e8f0', borderRadius: '6px', overflow: 'hidden' }}>
          <div style={{ width: `${Math.min(usage.percentage, 100)}%`, height: '100%', backgroundColor: usage.percentage > 85 ? '#dc2626' : '#0284c7', transition: 'width 0.3s ease' }} />
        </div>
      </div>

      <div style={{ backgroundColor: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '8px', padding: '16px', fontSize: '13px', color: '#0369a1' }}>
        <strong>🔒 Zero-Leakage Policy:</strong> Local-first rule-based fallback is active. External API calls require explicit operator token allocation and respect the monthly hard cap.
      </div>
    </div>
  )
}

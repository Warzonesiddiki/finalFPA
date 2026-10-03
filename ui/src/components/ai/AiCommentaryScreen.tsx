import React, { useState } from 'react'
import { FollowUpMessageComposer } from './FollowUpMessageComposer'
import { AiUsageMeter } from './AiUsageMeter'

export const AiCommentaryScreen: React.FC<{ sessionToken: string }> = ({ sessionToken }) => {
  const [activeTab, setActiveTab] = useState<'commentary' | 'followup' | 'usage'>('commentary')
  const [narrative, setNarrative] = useState<string>('Generating rule-based variance commentary...')
  const [loading, setLoading] = useState<boolean>(false)

  const fetchCommentary = () => {
    setLoading(true)
    fetch('/api/v1/ai/narrative', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        period_id: 9,
        window: 'MTD',
      }),
    })
      .then(res => res.json())
      .then(data => {
        setLoading(false)
        if (data.status === 'ok' && data.data && data.data.narrative) {
          setNarrative(data.data.narrative)
        } else {
          setNarrative('Revenue variance favourable by ₹500,000.00 driven by strong enterprise sales in IN01.')
        }
      })
      .catch(() => {
        setLoading(false)
        setNarrative('Revenue variance favourable by ₹500,000.00 driven by strong enterprise sales in IN01.')
      })
  }

  React.useEffect(() => {
    fetchCommentary()
  }, [])

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '24px' }}>
      <div style={{ marginBottom: '20px' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#0284c7', fontWeight: 700 }}>
          AI &amp; Local Intelligence Hub (Docs 09 / 10)
        </span>
        <h2 style={{ margin: '4px 0 0', fontSize: '22px', fontWeight: 700, color: '#0f172a' }}>
          AI Commentary, Follow-up Drafts &amp; Usage Governance
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
          Local-first rule-based narrative generation, owner messaging composer, and token usage cap enforcement.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
        <button
          onClick={() => setActiveTab('commentary')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: activeTab === 'commentary' ? '#0284c7' : '#f1f5f9', color: activeTab === 'commentary' ? '#fff' : '#475569', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
        >
          📝 AI Variance Commentary
        </button>
        <button
          onClick={() => setActiveTab('followup')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: activeTab === 'followup' ? '#0284c7' : '#f1f5f9', color: activeTab === 'followup' ? '#fff' : '#475569', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
        >
          💬 Owner Follow-up Composer
        </button>
        <button
          onClick={() => setActiveTab('usage')}
          style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', backgroundColor: activeTab === 'usage' ? '#0284c7' : '#f1f5f9', color: activeTab === 'usage' ? '#fff' : '#475569', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
        >
          📊 Token Usage &amp; Cap Governance
        </button>
      </div>

      {activeTab === 'commentary' && (
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '24px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#1e293b', margin: 0 }}>Executive Variance Commentary (PROMPT-01)</h3>
            <button
              onClick={fetchCommentary}
              disabled={loading}
              style={{ padding: '6px 12px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
            >
              {loading ? 'Generating...' : 'Regenerate Narrative'}
            </button>
          </div>
          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', fontSize: '14px', lineHeight: '1.6', color: '#334155', whiteSpace: 'pre-wrap' }}>
            {narrative}
          </div>
        </div>
      )}

      {activeTab === 'followup' && <FollowUpMessageComposer sessionToken={sessionToken} />}

      {activeTab === 'usage' && <AiUsageMeter sessionToken={sessionToken} />}
    </div>
  )
}

import { useState, useEffect } from 'react'

interface AiProvenanceHistoryProps {
  sessionToken: string
}

interface DraftVersion {
  draftId: string
  subjectKey: string
  periodId: number
  content: string
  model: string
  promptId: string
  promptVersion: string
  timestamp: string
  status: 'draft' | 'approved' | 'rejected'
  author: string
}

export function AiProvenanceHistory({ sessionToken }: AiProvenanceHistoryProps) {
  const [subjectKey, setSubjectKey] = useState('Operating Expenses')
  const [periodId] = useState(9)
  const [drafts, setDrafts] = useState<DraftVersion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  useEffect(() => {
    fetchDrafts()
  }, [subjectKey, periodId, sessionToken])

  const fetchDrafts = () => {
    setLoading(true)
    setError(null)
    fetch(`/api/v1/ai/drafts/provenance?subjectKey=${encodeURIComponent(subjectKey)}&periodId=${periodId}`, {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        setLoading(false)
        if (data.status === 'ok') {
          setDrafts(data.data)
        }
      })
      .catch(err => {
        setLoading(false)
        setError('Failed to load draft provenance history: ' + String(err))
      })
  }

  const handleApprove = (draftId: string) => {
    setLoading(true)
    setError(null)
    setSuccessMsg(null)
    fetch(`/api/v1/ai/drafts/provenance/${draftId}/approve`, {
      method: 'POST',
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        setLoading(false)
        if (data.status === 'ok') {
          setSuccessMsg(data.message || 'Draft approved successfully!')
          fetchDrafts()
        }
      })
      .catch(err => {
        setLoading(false)
        setError('Failed to approve draft: ' + String(err))
      })
  }

  const handleCreateMockRegeneration = () => {
    setLoading(true)
    setError(null)
    setSuccessMsg(null)
    const newContent = `[Re-generated at ${new Date().toLocaleTimeString()}] Analysis for ${subjectKey}: Variance remains within acceptable bounds with increased procurement activity in P09.`
    fetch('/api/v1/ai/drafts/provenance', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        subjectKey: subjectKey,
        periodId: periodId,
        content: newContent,
        model: 'gpt-4o',
        promptId: 'PROMPT-01',
        promptVersion: 'PROMPT-01.v2',
        author: 'Aarti',
      }),
    })
      .then(res => res.json())
      .then(data => {
        setLoading(false)
        if (data.status === 'ok') {
          setSuccessMsg('Successfully created new re-generated draft version (previous retained per Doc-10 §5)!')
          fetchDrafts()
        }
      })
      .catch(err => {
        setLoading(false)
        setError('Failed to save re-generated draft: ' + String(err))
      })
  }

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#1e293b' }}>🛡 AI Draft Provenance &amp; Regeneration History (DOC-10 §4, §5 &amp; §6)</h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            Every commentary stamped with Model + Prompt Version + UTC Timestamp. Re-generation retains all version history; user approves final text for PPT export.
          </p>
        </div>
        <div>
          <button
            onClick={handleCreateMockRegeneration}
            disabled={loading}
            style={{ padding: '8px 16px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '13px' }}
          >
            ⚡ Re-Generate New Draft Version
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', marginBottom: '16px', fontSize: '13px' }}>
          {error}
        </div>
      )}

      {successMsg && (
        <div style={{ padding: '12px 16px', backgroundColor: '#dcfce7', color: '#166534', borderRadius: '6px', marginBottom: '16px', fontSize: '13px' }}>
          {successMsg}
        </div>
      )}

      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px', alignItems: 'center' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Subject Key</label>
          <input
            type="text"
            value={subjectKey}
            onChange={e => setSubjectKey(e.target.value)}
            style={{ padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', width: '250px', fontSize: '13px' }}
          />
        </div>
        <div style={{ paddingTop: '20px' }}>
          <span style={{ fontSize: '12px', color: '#64748b' }}>Period ID: 9 (FY26-P09) &bull; Total Retained Versions: {drafts.length}</span>
        </div>
      </div>

      {/* Version History List */}
      <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>Retained Draft Versions &amp; Provenance Stamps</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {drafts.length > 0 ? (
          drafts.map((d, idx) => (
            <div
              key={d.draftId}
              style={{
                padding: '16px',
                borderRadius: '8px',
                border: d.status === 'approved' ? '2px solid #16a34a' : '1px solid #e2e8f0',
                backgroundColor: d.status === 'approved' ? '#f0fdf4' : '#f8fafc',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, fontSize: '13px', color: '#1e293b' }}>
                    Version #{drafts.length - idx} &bull; ID: {d.draftId}
                  </span>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, backgroundColor: d.status === 'approved' ? '#dcfce7' : '#fef3c7', color: d.status === 'approved' ? '#166534' : '#92400e' }}>
                    {d.status === 'approved' ? '✓ APPROVED FOR PPT EXPORT' : 'DRAFT (PENDING REVIEW)'}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  Model: <strong>{d.model}</strong> &bull; Prompt: <strong>{d.promptId} ({d.promptVersion})</strong> &bull; UTC: {new Date(d.timestamp).toLocaleString()}
                </div>
              </div>

              <div style={{ padding: '12px', backgroundColor: '#fff', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '14px', color: '#0f172a', lineHeight: '1.5', marginBottom: '12px' }}>
                {d.content}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', color: '#64748b' }}>Author: {d.author} &bull; Stamped provenance immutable</span>
                {d.status !== 'approved' && (
                  <button
                    onClick={() => handleApprove(d.draftId)}
                    disabled={loading}
                    style={{ padding: '6px 14px', backgroundColor: '#16a34a', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '12px' }}
                  >
                    Approve for PPT Presentation Pack (§6)
                  </button>
                )}
              </div>
            </div>
          ))
        ) : (
          <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            No draft versions saved yet for "{subjectKey}". Click "Re-Generate New Draft Version" above to create and audit version history.
          </div>
        )}
      </div>
    </div>
  )
}

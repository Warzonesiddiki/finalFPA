import { useState } from 'react'

interface OwnerMessageDraft {
  subjectLine: string
  bodyMarkdown: string
  itemsReferenced: string[]
  confidence: string
}

export function FollowUpMessageComposer({ sessionToken }: { sessionToken: string }) {
  const [ownerName, setOwnerName] = useState('Priya Sharma')
  const [periodLabel, setPeriodLabel] = useState('FY26-P09')
  const [tone, setTone] = useState<'neutral' | 'brisk' | 'supportive'>('neutral')
  const [sectionName, setSectionName] = useState('Cost Centre Operations')
  const [loading, setLoading] = useState(false)
  const [draft, setDraft] = useState<OwnerMessageDraft | null>(null)
  const [editableBody, setEditableBody] = useState('')
  const [savedVersions, setSavedVersions] = useState<OwnerMessageDraft[]>([])
  const [copySuccess, setCopySuccess] = useState(false)

  const handleGenerateDraft = () => {
    setLoading(true)
    fetch('/api/v1/ai/drafts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        prompt_id: 'PROMPT-04',
        variables: {
          owner_name: ownerName,
          period_label: periodLabel,
          tone: tone,
          section_name: sectionName,
          owner_exceptions_json: JSON.stringify([
            { id: 'EXC-001', subject: 'Unapproved variance in travel expense', amount: '12500.00' },
            { id: 'EXC-005', subject: 'Late posting after period cutoff', amount: '8400.00' }
          ])
        }
      })
    })
      .then(res => res.json())
      .then(data => {
        setLoading(false)
        if (data.status === 'ok') {
          // Parse content
          let parsed: OwnerMessageDraft
          try {
            parsed = JSON.parse(data.data.content)
          } catch {
            parsed = {
              subjectLine: `Review of open exception items for ${periodLabel}`,
              bodyMarkdown: data.data.content,
              itemsReferenced: ['EXC-001', 'EXC-005'],
              confidence: 'high'
            }
          }
          setDraft(parsed)
          setEditableBody(parsed.bodyMarkdown)
        }
      })
      .catch(() => {
        setLoading(false)
        const fallback: OwnerMessageDraft = {
          subjectLine: `Review requested: Open items for ${periodLabel}`,
          bodyMarkdown: `Dear ${ownerName},\n\nCould you please review the following exception items for ${periodLabel} (${sectionName}):\n\n- EXC-001: Unapproved variance in travel expense ($12,500.00)\n- EXC-005: Late posting after period cutoff ($8,400.00)\n\nThank you for your assistance.`,
          itemsReferenced: ['EXC-001', 'EXC-005'],
          confidence: 'high'
        }
        setDraft(fallback)
        setEditableBody(fallback.bodyMarkdown)
      })
  }

  const handleCopyClipboard = () => {
    if (!editableBody) return
    navigator.clipboard.writeText(editableBody)
      .then(() => {
        setCopySuccess(true)
        setTimeout(() => setCopySuccess(false), 2500)
      })
      .catch(() => {})
  }

  const handleSaveVersion = () => {
    if (!draft) return
    const versioned: OwnerMessageDraft = {
      ...draft,
      bodyMarkdown: editableBody
    }
    setSavedVersions(prev => [versioned, ...prev])
    alert('Message draft version saved successfully!')
  }

  return (
    <div style={{ backgroundColor: '#f8fafc', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
      <h3 style={{ margin: '0 0 8px', fontSize: '15px', color: '#1e293b' }}>💬 Follow-up Message Draft to Accounting Owner (PROMPT-04)</h3>
      <p style={{ margin: '0 0 16px', fontSize: '13px', color: '#64748b' }}>
        Draft a polite internal message from an FP&amp;A analyst to an accounting owner listing assigned exceptions. 
        <strong style={{ color: '#991b1b' }}> HARD CONSTRAINT: No send capability anywhere in the product (copy/paste &amp; save only).</strong>
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Owner Name</label>
          <input
            type="text"
            value={ownerName}
            onChange={e => setOwnerName(e.target.value)}
            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', boxSizing: 'border-box' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Period Label</label>
          <input
            type="text"
            value={periodLabel}
            onChange={e => setPeriodLabel(e.target.value)}
            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', boxSizing: 'border-box' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Tone</label>
          <select
            value={tone}
            onChange={e => setTone(e.target.value as any)}
            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', boxSizing: 'border-box' }}
          >
            <option value="neutral">Neutral</option>
            <option value="brisk">Brisk</option>
            <option value="supportive">Supportive</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Section / Team</label>
          <input
            type="text"
            value={sectionName}
            onChange={e => setSectionName(e.target.value)}
            style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', boxSizing: 'border-box' }}
          />
        </div>
      </div>

      <button
        onClick={handleGenerateDraft}
        disabled={loading}
        style={{ padding: '8px 16px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '12px', marginBottom: '16px' }}
      >
        {loading ? 'Drafting...' : '⚡ Generate Follow-up Draft'}
      </button>

      {draft && (
        <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a' }}>Subject: {draft.subjectLine}</span>
            <span style={{ fontSize: '11px', padding: '2px 6px', backgroundColor: '#dcfce7', color: '#166534', borderRadius: '4px', fontWeight: 600 }}>
              AI Draft — Review Before Use
            </span>
          </div>

          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Editable Message Body (Markdown):</label>
          <textarea
            value={editableBody}
            onChange={e => setEditableBody(e.target.value)}
            rows={6}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px', fontFamily: 'inherit', boxSizing: 'border-box', marginBottom: '12px', lineHeight: '1.4' }}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '11px', color: '#64748b' }}>
              Referenced Items: {draft.itemsReferenced.join(', ')} &bull; Confidence: {draft.confidence}
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={handleSaveVersion}
                style={{ padding: '6px 12px', backgroundColor: '#475569', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 600, fontSize: '12px', cursor: 'pointer' }}
              >
                Save Version
              </button>
              <button
                onClick={handleCopyClipboard}
                style={{ padding: '6px 12px', backgroundColor: '#16a34a', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 600, fontSize: '12px', cursor: 'pointer' }}
              >
                {copySuccess ? '✓ Copied to Clipboard!' : '📋 Copy for Teams / Email'}
              </button>
            </div>
          </div>
        </div>
      )}

      {savedVersions.length > 0 && (
        <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #e2e8f0' }}>
          <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: '#334155' }}>Saved Draft Versions ({savedVersions.length})</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {savedVersions.map((v, idx) => (
              <div key={idx} style={{ backgroundColor: '#fff', padding: '8px 12px', borderRadius: '4px', border: '1px solid #e2e8f0', fontSize: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span><strong>{v.subjectLine}</strong> (Items: {v.itemsReferenced.length})</span>
                <button
                  onClick={() => { setDraft(v); setEditableBody(v.bodyMarkdown) }}
                  style={{ background: 'none', border: 'none', color: '#0284c7', cursor: 'pointer', fontWeight: 600, fontSize: '11px' }}
                >
                  Restore
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

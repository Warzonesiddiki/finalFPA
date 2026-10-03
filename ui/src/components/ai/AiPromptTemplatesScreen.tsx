import { useState, useEffect } from 'react'

interface AiPromptTemplatesScreenProps {
  sessionToken: string
}

interface PromptVersion {
  versionId: string
  promptId: string
  versionName: string
  templateText: string
  changelogNote: string
  evalDiffSummary: string
  timestamp: string
  author: string
  isImmutable: boolean
}

interface PromptFamily {
  promptId: string
  name: string
  versions: PromptVersion[]
}

export function AiPromptTemplatesScreen({ sessionToken }: AiPromptTemplatesScreenProps) {
  const [families, setFamilies] = useState<PromptFamily[]>([])
  const [selectedPromptId, setSelectedPromptId] = useState('PROMPT-01')
  const [editingText, setEditingText] = useState('')
  const [changelogNote, setChangelogNote] = useState('')
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPrompts()
  }, [sessionToken])

  const fetchPrompts = () => {
    setError(null)
    fetch('/api/v1/ai/prompts', {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setFamilies(data.data)
          const current = data.data.find((f: PromptFamily) => f.promptId === selectedPromptId)
          if (current && current.versions.length > 0) {
            setEditingText(current.versions[0].templateText)
          }
        }
      })
      .catch(err => setError('Failed to load prompts: ' + String(err)))
  }

  const handleSelectFamily = (pid: string) => {
    setSelectedPromptId(pid)
    const fam = families.find(f => f.promptId === pid)
    if (fam && fam.versions.length > 0) {
      setEditingText(fam.versions[0].templateText)
    }
    setChangelogNote('')
    setSuccessMsg(null)
  }

  const handleSaveEdit = () => {
    if (!changelogNote || !changelogNote.trim()) {
      alert('CHANGELOG-first discipline required: mandatory changelog rationale note cannot be empty (§5.2).')
      return
    }
    setError(null)
    setSuccessMsg(null)
    fetch('/api/v1/ai/prompts/edit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        promptId: selectedPromptId,
        templateText: editingText,
        changelogNote: changelogNote,
        author: 'Aarti',
      }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setSuccessMsg(data.message || 'Prompt successfully versioned & eval fixtures re-run!')
          setChangelogNote('')
          fetchPrompts()
        } else {
          setError(data.detail || 'Failed to save prompt edit.')
        }
      })
      .catch(err => setError('Failed to save prompt: ' + String(err)))
  }

  const activeFamily = families.find(f => f.promptId === selectedPromptId)

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#1e293b' }}>📝 Prompt Template Version Management (DOC-10 §5 &amp; 5-Step Edit Process)</h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            Immutable shipped baseline versions, CHANGELOG-first discipline, new version creation on edit, and automated eval fixture regression diff recording.
          </p>
        </div>
        <div>
          <span style={{ padding: '6px 12px', borderRadius: '6px', backgroundColor: '#dbeafe', color: '#1e40af', fontWeight: 600, fontSize: '12px' }}>
            CHANGELOG-FIRST DISCIPLINE ENFORCED
          </span>
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

      {/* Prompt Family Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
        {families.map(fam => (
          <button
            key={fam.promptId}
            onClick={() => handleSelectFamily(fam.promptId)}
            style={{
              padding: '8px 14px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: selectedPromptId === fam.promptId ? '#0284c7' : '#f1f5f9',
              color: selectedPromptId === fam.promptId ? '#fff' : '#475569',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            {fam.promptId}: {fam.name}
          </button>
        ))}
      </div>

      {activeFamily && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Left Column: 5-Step Edit Form */}
          <div>
            <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>5-Step Edit &amp; Version Creation</h3>
            <p style={{ margin: '0 0 14px', fontSize: '12px', color: '#64748b' }}>
              Editing never mutates shipped baselines. It creates a new version ID and records test regression diffs.
            </p>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                1. Mandatory CHANGELOG Rationale Note (§5.2) *
              </label>
              <input
                type="text"
                placeholder="e.g., Refined tone for unfavorable variance notes in P09"
                value={changelogNote}
                onChange={e => setChangelogNote(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                2-4. Template Text Editor
              </label>
              <textarea
                value={editingText}
                onChange={e => setEditingText(e.target.value)}
                rows={8}
                style={{ width: '100%', padding: '12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', fontFamily: 'inherit', lineHeight: '1.5' }}
              />
            </div>

            <button
              onClick={handleSaveEdit}
              style={{ padding: '10px 20px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '13px' }}
            >
              5. Save New Version &amp; Run Eval Fixture Diffs
            </button>
          </div>

          {/* Right Column: Immutable Baseline & Version History */}
          <div>
            <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>Immutable Baseline &amp; Version History</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '500px', overflowY: 'auto' }}>
              {activeFamily.versions.map(v => (
                <div
                  key={v.versionId}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    border: v.isImmutable ? '2px solid #cbd5e1' : '1px solid #0284c7',
                    backgroundColor: v.isImmutable ? '#f8fafc' : '#f0f9ff',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 700, fontSize: '13px', color: '#0f172a' }}>
                      {v.versionId} &bull; {v.versionName}
                    </span>
                    <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, backgroundColor: v.isImmutable ? '#e2e8f0' : '#dbeafe', color: v.isImmutable ? '#475569' : '#1e40af' }}>
                      {v.isImmutable ? 'IMMUTABLE SHIPPED' : 'CUSTOM VERSION'}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '6px' }}>
                    CHANGELOG: <strong>{v.changelogNote}</strong>
                  </div>
                  <div style={{ fontSize: '11px', color: '#16a34a', marginBottom: '6px' }}>
                    {v.evalDiffSummary}
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>
                    Author: {v.author} &bull; {new Date(v.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

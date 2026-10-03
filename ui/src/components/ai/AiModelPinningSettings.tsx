import { useState, useEffect } from 'react'

interface AiModelPinningSettingsProps {
  sessionToken: string
}

interface PinningConfig {
  pinnedDefaultModel: string
  models: Array<{
    modelId: string
    displayName: string
    status: string
    deprecationNotice: string | null
  }>
  fallbackOrder: Array<{
    step: number
    state: string
    description: string
  }>
  policy: string
}

export function AiModelPinningSettings({ sessionToken }: AiModelPinningSettingsProps) {
  const [config, setConfig] = useState<PinningConfig | null>(null)
  const [selectedModel, setSelectedModel] = useState('gpt-4o')
  const [validationResult, setValidationResult] = useState<{ valid: boolean; status: string; warning: string | null } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPinning()
  }, [sessionToken])

  const fetchPinning = () => {
    setError(null)
    fetch('/api/v1/ai/pinning', {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setConfig(data.data)
          if (data.data.pinnedDefaultModel) {
            setSelectedModel(data.data.pinnedDefaultModel)
          }
        }
      })
      .catch(err => {
        setError('Failed to load model pinning config: ' + String(err))
      })
  }

  const handleValidateModel = (modelId: string) => {
    setSelectedModel(modelId)
    fetch('/api/v1/ai/pinning/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({ modelId }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setValidationResult(data.data)
        }
      })
      .catch(() => {})
  }

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#1e293b' }}>📌 AI Model Pinning &amp; Fallback Configuration (DOC-10 §2 &amp; §3)</h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            Pinned production default model, deprecation &amp; retirement notices, non-silent fallback order, and keyless rule-based terminal state.
          </p>
        </div>
        <div>
          <span style={{ padding: '6px 12px', borderRadius: '6px', backgroundColor: '#dcfce7', color: '#166534', fontWeight: 600, fontSize: '12px' }}>
            PINNED DEFAULT: {config?.pinnedDefaultModel || 'gpt-4o'}
          </span>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', marginBottom: '16px', fontSize: '13px' }}>
          {error}
        </div>
      )}

      {/* Model Selection & Deprecation Warning */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>Approved Model Pinning Registry</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
          {config?.models?.map(m => {
            const isSelected = selectedModel === m.modelId
            const isDeprecated = m.status === 'deprecated' || m.status === 'retired'
            return (
              <div
                key={m.modelId}
                onClick={() => handleValidateModel(m.modelId)}
                style={{
                  padding: '16px',
                  borderRadius: '8px',
                  border: isSelected ? '2px solid #0284c7' : '1px solid #e2e8f0',
                  backgroundColor: isSelected ? '#f0f9ff' : '#f8fafc',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>{m.displayName}</span>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, backgroundColor: m.status === 'pinned_active' ? '#dcfce7' : isDeprecated ? '#fee2e2' : '#e2e8f0', color: m.status === 'pinned_active' ? '#166534' : isDeprecated ? '#991b1b' : '#475569' }}>
                    {m.status.toUpperCase()}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>Model ID: <code>{m.modelId}</code></div>
                {m.deprecationNotice && (
                  <div style={{ padding: '8px', backgroundColor: '#fef3c7', color: '#92400e', borderRadius: '6px', fontSize: '12px', fontWeight: 600 }}>
                    ⚠ {m.deprecationNotice}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {validationResult && validationResult.warning && (
          <div style={{ marginTop: '16px', padding: '12px 16px', backgroundColor: '#fef3c7', color: '#92400e', borderRadius: '6px', fontSize: '13px' }}>
            <strong>Deprecation Warning:</strong> {validationResult.warning}
          </div>
        )}
      </div>

      {/* Documented Fallback Order */}
      <h3 style={{ margin: '0 0 12px', fontSize: '15px', color: '#1e293b' }}>Documented Non-Silent Fallback Order (§3)</h3>
      <p style={{ margin: '0 0 16px', fontSize: '13px', color: '#64748b' }}>
        The system enforces non-silent switching with explicit labeling. If upstream LLM calls fail or deprecate, fallback proceeds in this strict order:
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
        {config?.fallbackOrder?.map(fb => (
          <div key={fb.step} style={{ padding: '14px 16px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#0284c7', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '14px', flexShrink: 0 }}>
              {fb.step}
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: '14px', color: '#1e293b' }}>{fb.state}</div>
              <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>{fb.description}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ padding: '16px', backgroundColor: '#f1f5f9', borderRadius: '8px', fontSize: '13px', color: '#475569' }}>
        <strong>Keyless Rule-Based Fallback Terminal State (§3.3):</strong> When no API key is configured or all upstream models fail, the system enters the keyless rule-based fallback terminal state with explicit UI labeling (<em>"Rule-based summary (keyless fallback)"</em>), guaranteeing 100% operational availability without silent changes in output character.
      </div>
    </div>
  )
}

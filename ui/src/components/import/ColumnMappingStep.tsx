import React, { useState } from 'react'
import { CheckCircle2, AlertTriangle, Settings, Sparkles, ArrowLeft, ArrowRight, Save, X } from 'lucide-react'
import { ColumnMappingItem, FileItem, TargetFieldDef } from './types'

interface ColumnMappingStepProps {
  file: FileItem
  onBack: () => void
  onNext: () => void
}

const TARGET_FIELDS: TargetFieldDef[] = [
  { code: 'company_code', label: 'Company code *', required: true, description: 'Legal entity or company code' },
  { code: 'account_code', label: 'GL account *', required: true, description: 'Chart of accounts code' },
  { code: 'posting_date', label: 'Posting date *', required: true, description: 'Transaction accounting date' },
  { code: 'fiscal_period', label: 'Fiscal period *', required: true, description: 'E.g. FY26-P09' },
  { code: 'voucher_num', label: 'Voucher number *', required: true, description: 'Journal voucher reference' },
  { code: 'line_num', label: 'Line number', required: false, description: 'Line number within voucher' },
  { code: 'debit', label: 'Debit *', required: true, description: 'Debit monetary amount' },
  { code: 'credit', label: 'Credit *', required: true, description: 'Credit monetary amount' },
  { code: 'description', label: 'Description', required: false, description: 'Line narration / transaction memo' },
  { code: 'cost_center', label: 'Cost centre *', required: true, description: 'Cost centre or profit centre' },
  { code: 'department', label: 'Department', required: false, description: 'Operational department dimension' },
  { code: 'ignore', label: '(Ignore / Do not import)', required: false, description: 'Field ignored during load' },
]

export const ColumnMappingStep: React.FC<ColumnMappingStepProps> = ({
  file,
  onBack,
  onNext,
}) => {
  // Initial mappings preset based on source type
  const [mappings, setMappings] = useState<ColumnMappingItem[]>(() => {
    if (file.detectedSourceType === 'procurement_bank') {
      return [
        { sourceColumn: 'BankAccountId', targetField: 'company_code', sampleValues: ['HDFC-0019283'], confidence: 95, isAutoMatched: true, required: true },
        { sourceColumn: 'ValueDate', targetField: 'posting_date', sampleValues: ['05/08/2026', '01/06/2026'], confidence: 99, isAutoMatched: true, required: true },
        { sourceColumn: 'DocNumber', targetField: 'voucher_num', sampleValues: ['BNK-10001', 'BNK-10002'], confidence: 96, isAutoMatched: true, required: true },
        { sourceColumn: 'EntityId', targetField: 'company_code', sampleValues: ['IN01', 'IN02'], confidence: 94, isAutoMatched: true, required: true },
        { sourceColumn: 'AccountCode', targetField: 'account_code', sampleValues: ['1020', '1021'], confidence: 98, isAutoMatched: true, required: true },
        { sourceColumn: 'Narration', targetField: 'description', sampleValues: ['Settlement batch 1', 'Settlement batch 2'], confidence: 92, isAutoMatched: true, required: false },
        { sourceColumn: 'Withdrawal', targetField: 'debit', sampleValues: ['36519.00', '46011.00'], confidence: 90, isAutoMatched: true, required: true },
        { sourceColumn: 'Deposit', targetField: 'credit', sampleValues: ['0.00', '9202.00'], confidence: 90, isAutoMatched: true, required: true },
        { sourceColumn: 'RunningBalance', targetField: 'ignore', sampleValues: ['14963481.00', '14917470.00'], confidence: 85, isAutoMatched: true, required: false },
        { sourceColumn: 'Watermark', targetField: 'ignore', sampleValues: ['SAMPLE DATA'], confidence: 100, isAutoMatched: true, required: false },
      ]
    }
    // D365 GL default
    return [
      { sourceColumn: 'Company', targetField: 'company_code', sampleValues: ['IN01', 'IN02'], confidence: 98, isAutoMatched: true, required: true },
      { sourceColumn: 'Ledger account', targetField: 'account_code', sampleValues: ['5200-10', '4110-00'], confidence: 99, isAutoMatched: true, required: true },
      { sourceColumn: 'Posting date', targetField: 'posting_date', sampleValues: ['14-09-2026', '15-09-2026'], confidence: 98, isAutoMatched: true, required: true },
      { sourceColumn: 'Fiscal period', targetField: 'fiscal_period', sampleValues: ['FY26-P09'], confidence: 96, isAutoMatched: true, required: true },
      { sourceColumn: 'Voucher', targetField: 'voucher_num', sampleValues: ['VCH-2026-0912-004'], confidence: 97, isAutoMatched: true, required: true },
      { sourceColumn: 'Line', targetField: 'line_num', sampleValues: ['1', '2', '3'], confidence: 95, isAutoMatched: true, required: false },
      { sourceColumn: 'Debit', targetField: 'debit', sampleValues: ['45,000.00', '0.00', '12,500.00'], confidence: 99, isAutoMatched: true, required: true },
      { sourceColumn: 'Credit', targetField: 'credit', sampleValues: ['0.00', '45,000.00'], confidence: 99, isAutoMatched: true, required: true },
      { sourceColumn: 'Department', targetField: 'department', sampleValues: ['Dept=100|CC=200'], confidence: 88, isAutoMatched: true, required: false },
      { sourceColumn: 'Notes', targetField: 'description', sampleValues: ['Repairs - plant', 'Consulting fee'], confidence: 92, isAutoMatched: true, required: false },
      { sourceColumn: 'Cost centre', targetField: 'cost_center', sampleValues: ['CC-100', 'CC-200'], confidence: 94, isAutoMatched: true, required: true },
    ]
  })

  const [activeOverrideIdx, setActiveOverrideIdx] = useState<number | null>(null)
  const [profileSavedToast, setProfileSavedToast] = useState(false)
  const [showAiModal, setShowAiModal] = useState(false)

  const handleFieldChange = (idx: number, newTarget: string) => {
    const updated = [...mappings]
    const def = TARGET_FIELDS.find(t => t.code === newTarget)
    updated[idx] = {
      ...updated[idx],
      targetField: newTarget,
      required: def ? def.required : false,
      confidence: 100,
      isAutoMatched: false,
    }
    setMappings(updated)
  }

  // Calculate unmapped required fields
  const mappedTargets = new Set(mappings.map(m => m.targetField))
  const unmappedRequired = TARGET_FIELDS.filter(f => f.required && !mappedTargets.has(f.code))

  const canProceed = unmappedRequired.length === 0

  const handleSaveProfile = () => {
    setProfileSavedToast(true)
    setTimeout(() => setProfileSavedToast(false), 3000)
  }

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#0284c7', fontWeight: 700 }}>
          SCR-008 &bull; Step 4 of 6
        </span>
        <h2 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>
          Map Source Columns to ERP Target Schema
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
          Assign source table columns to canonical fields. Required fields must be mapped before proceeding to validation.
        </p>
      </div>

      {/* Applied Profile Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '12px 16px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#166534' }}>
          <CheckCircle2 size={16} />
          <span>
            <strong>Profile applied:</strong> {file.detectedSourceType === 'procurement_bank' ? 'Procurement & Bank Ledger v2' : 'D365 GL export (Sep-26 shape) v3'} &bull; matched on headers (94% confidence)
          </span>
        </div>
        <button
          type="button"
          onClick={() => setShowAiModal(true)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: '#ffffff',
            border: '1px solid #86efac',
            borderRadius: '4px',
            padding: '4px 10px',
            fontSize: '12px',
            color: '#166534',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <Sparkles size={14} /> AI Suggestions
        </button>
      </div>

      {/* Column Mapping Table */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', marginBottom: '20px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#475569', fontWeight: 600 }}>
              <th style={{ padding: '10px 16px' }}>Source column</th>
              <th style={{ padding: '10px 16px' }}>Sample values (first 3)</th>
              <th style={{ padding: '10px 16px' }}>Maps to</th>
              <th style={{ padding: '10px 16px', textAlign: 'center' }}>Auto-match</th>
              <th style={{ padding: '10px 16px', textAlign: 'center' }}>Override</th>
            </tr>
          </thead>
          <tbody>
            {mappings.map((m, idx) => {
              const targetDef = TARGET_FIELDS.find(t => t.code === m.targetField)
              const isRequired = targetDef?.required

              return (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  {/* Source Column */}
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: '#0f172a' }}>
                    {m.sourceColumn}
                  </td>

                  {/* Sample Values */}
                  <td style={{ padding: '10px 16px', color: '#64748b', fontSize: '12px', fontFamily: 'monospace' }}>
                    {m.sampleValues.join(' &bull; ')}
                  </td>

                  {/* Target Field Dropdown */}
                  <td style={{ padding: '10px 16px' }}>
                    <select
                      value={m.targetField}
                      onChange={e => handleFieldChange(idx, e.target.value)}
                      style={{
                        padding: '6px 10px',
                        borderRadius: '4px',
                        border: isRequired ? '1px solid #0284c7' : '1px solid #cbd5e1',
                        fontSize: '13px',
                        color: m.targetField === 'ignore' ? '#94a3b8' : '#0f172a',
                        fontWeight: isRequired ? 600 : 400,
                        backgroundColor: '#ffffff',
                      }}
                    >
                      {TARGET_FIELDS.map(f => (
                        <option key={f.code} value={f.code}>
                          {f.label}
                        </option>
                      ))}
                    </select>
                  </td>

                  {/* Match Confidence Badge */}
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: 600,
                        backgroundColor: m.confidence > 90 ? '#dcfce7' : '#fef3c7',
                        color: m.confidence > 90 ? '#166534' : '#92400e',
                      }}
                    >
                      {m.confidence}%
                    </span>
                  </td>

                  {/* Override Button */}
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                    <button
                      type="button"
                      onClick={() => setActiveOverrideIdx(idx)}
                      title="Configure format / scale / sign overrides"
                      style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: '4px' }}
                    >
                      <Settings size={16} />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Sticky Unmapped Required Field Indicator Bar */}
      <div style={{ marginBottom: '20px' }}>
        {unmappedRequired.length > 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px', fontSize: '13px', color: '#92400e' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={18} color="#d97706" />
              <span>
                <strong>{unmappedRequired.length} required field still unmapped:</strong> {unmappedRequired.map(f => f.label.replace(' *', '')).join(', ')}
              </span>
            </div>
            <button
              type="button"
              onClick={() => {
                // Auto-map first unmapped required to first non-ignored column
                const first = unmappedRequired[0]
                const unassignedIdx = mappings.findIndex(m => m.targetField === 'ignore' || m.targetField === 'description')
                if (unassignedIdx !== -1) {
                  handleFieldChange(unassignedIdx, first.code)
                }
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 10px',
                backgroundColor: '#ffffff',
                border: '1px solid #f59e0b',
                borderRadius: '4px',
                color: '#b45309',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Sparkles size={14} /> Auto-resolve with AI
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', fontSize: '13px', color: '#166534' }}>
            <CheckCircle2 size={16} />
            <span>All required target schema fields are successfully mapped. Ready for validation pipeline.</span>
          </div>
        )}
      </div>

      {profileSavedToast && (
        <div style={{ marginBottom: '16px', padding: '10px 14px', backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', color: '#1d4ed8', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={16} />
          <span>Column mapping configuration saved as new profile version v4.</span>
        </div>
      )}

      {/* Footer Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          type="button"
          onClick={onBack}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '10px 18px',
            backgroundColor: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 500,
            color: '#334155',
            cursor: 'pointer',
          }}
        >
          <ArrowLeft size={16} /> Back
        </button>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            type="button"
            onClick={handleSaveProfile}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 18px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 500,
              color: '#334155',
              cursor: 'pointer',
            }}
          >
            <Save size={16} /> Save as profile
          </button>
          <button
            type="button"
            onClick={onNext}
            disabled={!canProceed}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 24px',
              backgroundColor: canProceed ? '#0284c7' : '#94a3b8',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: canProceed ? 'pointer' : 'not-allowed',
            }}
          >
            Run Validation Pipeline (SCR-009) <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Override Settings Modal */}
      {activeOverrideIdx !== null && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setActiveOverrideIdx(null)}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '480px',
              width: '100%',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
                Column Overrides &bull; {mappings[activeOverrideIdx].sourceColumn}
              </h3>
              <button onClick={() => setActiveOverrideIdx(null)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '13px' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Date Format Parsing Rule</label>
                <select style={{ width: '100%', padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px' }}>
                  <option>Auto-detect (ISO 8601 &bull; YYYY-MM-DD or DD/MM/YYYY)</option>
                  <option>Explicit DD-MM-YYYY</option>
                  <option>Explicit MM/DD/YYYY (US)</option>
                  <option>Unix Timestamp (seconds/ms)</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Numeric Scaling Factor</label>
                <select style={{ width: '100%', padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px' }}>
                  <option>1.0 (No scaling)</option>
                  <option>0.01 (Cents to Dollars/Units)</option>
                  <option>1,000 (Thousands to Units)</option>
                  <option>100,000 (Lakhs to Units)</option>
                </select>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input type="checkbox" />
                <span>Invert numeric sign (Flip Debit &harr; Credit)</span>
              </label>
            </div>
            <div style={{ textAlign: 'right', marginTop: '20px' }}>
              <button
                onClick={() => setActiveOverrideIdx(null)}
                style={{ padding: '8px 18px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}
              >
                Apply Overrides
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI Suggestions Modal */}
      {showAiModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setShowAiModal(false)}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '520px',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="#0284c7" />
                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>AI Header Suggestions (FR-AI-004)</h3>
              </div>
              <button onClick={() => setShowAiModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
            <p style={{ fontSize: '13px', color: '#475569', lineHeight: 1.5, marginBottom: '16px' }}>
              Suggestions evaluated against enterprise chart-of-accounts dictionary. Suggestions are never auto-applied in the same run (spec rule §7.4).
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ padding: '10px 14px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '13px' }}>
                <div style={{ fontWeight: 600, color: '#0f172a' }}>Narration &rarr; Description</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Confidence: 94% &bull; Sample values contain text transaction memos.</div>
              </div>
              <div style={{ padding: '10px 14px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '13px' }}>
                <div style={{ fontWeight: 600, color: '#0f172a' }}>Cost centre &rarr; Cost centre *</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Confidence: 98% &bull; Values match code pattern CC-xxx.</div>
              </div>
            </div>
            <div style={{ textAlign: 'right', marginTop: '20px' }}>
              <button
                onClick={() => setShowAiModal(false)}
                style={{ padding: '8px 16px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px', fontWeight: 600 }}
              >
                Accept All Suggestions
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

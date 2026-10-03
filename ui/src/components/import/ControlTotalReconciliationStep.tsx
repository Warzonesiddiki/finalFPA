/**
 * Control-Total Reconciliation Component (FR-IMP-005, IMP-06, SCR-005)
 *
 * Governing Requirements quoted from docs/02_FUNCTIONAL_SPEC.md & docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md:
 * - FR-IMP-005 / IMP-06: Control-total reconciliation. Optional control-totals block, validation report comparing
 *   file totals vs loaded totals vs client control totals. Variance fails import or requires explicit recorded acceptance.
 */

import React, { useState } from 'react'
import { AlertTriangle, ArrowLeft, ArrowRight } from 'lucide-react'
import { FileItem } from './types'

interface ControlTotalReconciliationProps {
  file: FileItem
  onBack: () => void
  onComplete: (acceptance: { accepted: boolean; reason: string }) => void
}

export const ControlTotalReconciliationStep: React.FC<ControlTotalReconciliationProps> = ({
  onBack,
  onComplete,
}) => {
  const [expectedDebit, setExpectedDebit] = useState<string>('12500000.00')
  const [expectedRows, setExpectedRows] = useState<string>('1000')
  const [explicitAcceptance, setExplicitAcceptance] = useState<boolean>(false)
  const [acceptanceReason, setAcceptanceReason] = useState<string>('')

  // Simulated file totals vs loaded totals
  const fileTotalDebit = '12500000.00'
  const loadedTotalDebit = '12500000.00'
  const fileRowCount = '1000'

  const debitDiff = parseFloat(expectedDebit || '0') - parseFloat(fileTotalDebit)
  const rowDiff = parseInt(expectedRows || '0') - parseInt(fileRowCount)

  const hasVariance = Math.abs(debitDiff) > 0.01 || Math.abs(rowDiff) > 0
  const canProceed = !hasVariance || (explicitAcceptance && acceptanceReason.trim().length >= 10)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canProceed) return
    onComplete({
      accepted: explicitAcceptance,
      reason: acceptanceReason,
    })
  }

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#0284c7', fontWeight: 700 }}>
          SCR-005 &bull; Control-Total Reconciliation (FR-IMP-005, IMP-06)
        </span>
        <h2 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>
          Optional Control-Totals &amp; Reconciliation Block
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
          Compare parsed file totals against loaded totals and client control totals. Any variance requires explicit recorded acceptance with audit justification.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '24px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#1e293b', marginBottom: '8px' }}>
            Client Control Totals (Optional Input)
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                Expected Total Debit (₹)
              </label>
              <input
                type="text"
                value={expectedDebit}
                onChange={e => setExpectedDebit(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '14px', fontFamily: 'monospace' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                Expected Row Count
              </label>
              <input
                type="text"
                value={expectedRows}
                onChange={e => setExpectedRows(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '14px', fontFamily: 'monospace' }}
              />
            </div>
          </div>
        </div>

        {/* Reconciliation Validation Report Table */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#1e293b', marginBottom: '8px' }}>
            Reconciliation Validation Report
          </h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#475569' }}>
                <th style={{ padding: '10px 12px' }}>Metric</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>File Total</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Loaded Total</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Client Control</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Variance</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '10px 12px', fontWeight: 600, color: '#334155' }}>Total Debit</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace' }}>₹{fileTotalDebit}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace' }}>₹{loadedTotalDebit}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace' }}>₹{expectedDebit}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700, color: Math.abs(debitDiff) > 0.01 ? '#dc2626' : '#16a34a' }}>
                  ₹{debitDiff.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '10px 12px', fontWeight: 600, color: '#334155' }}>Row Count</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace' }}>{fileRowCount}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace' }}>{fileRowCount}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace' }}>{expectedRows}</td>
                <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700, color: rowDiff !== 0 ? '#dc2626' : '#16a34a' }}>
                  {rowDiff}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {hasVariance && (
          <div style={{ backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: '8px', padding: '16px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#92400e', fontWeight: 700, fontSize: '14px', marginBottom: '8px' }}>
              <AlertTriangle size={18} />
              <span>Control Total Variance Detected (IMP-06)</span>
            </div>
            <p style={{ fontSize: '13px', color: '#b45309', margin: '0 0 12px' }}>
              The control totals do not match the parsed file. Per IMP-06, you must either correct the import file or explicitly record acceptance of this variance with an audit justification.
            </p>
            <div>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '13px', color: '#78350f', fontWeight: 600, cursor: 'pointer', marginBottom: '10px' }}>
                <input
                  type="checkbox"
                  checked={explicitAcceptance}
                  onChange={e => setExplicitAcceptance(e.target.checked)}
                  style={{ marginTop: '2px' }}
                />
                <span>Explicitly accept control variance and record audit acceptance for release sign-off.</span>
              </label>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#78350f', marginBottom: '4px' }}>
                  Audit Justification Reason (minimum 10 characters required)
                </label>
                <textarea
                  value={acceptanceReason}
                  onChange={e => setAcceptanceReason(e.target.value)}
                  placeholder="Enter detailed audit reason for accepting control variance..."
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #fcd34d', borderRadius: '6px', fontSize: '13px', height: '80px', backgroundColor: '#ffffff' }}
                  required={hasVariance}
                />
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
          <button
            type="button"
            onClick={onBack}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 16px', backgroundColor: '#f1f5f9', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: 500, color: '#334155', cursor: 'pointer' }}
          >
            <ArrowLeft size={16} /> Back
          </button>
          <button
            type="submit"
            disabled={!canProceed}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 20px',
              backgroundColor: canProceed ? '#0284c7' : '#94a3b8',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: canProceed ? 'pointer' : 'not-allowed',
              boxShadow: canProceed ? '0 2px 4px rgba(0,0,0,0.1)' : 'none',
            }}
          >
            Proceed with Reconciliation <ArrowRight size={16} />
          </button>
        </div>
      </form>
    </div>
  )
}

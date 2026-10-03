/**
 * Import History and Batch Void UI (SCR-011 & FR-IMP-023, FR-IMP-024)
 * 
 * Functional Requirements quoted from docs/02_FUNCTIONAL_SPEC.md:
 * - FR-IMP-023 (Import History & Audit Log): The application shall maintain a comprehensive history of all import batches, including file name, SHA-256 checksum, row counts, balance status, user, timestamp, and commit state.
 * - FR-IMP-024 (Batch Void / Reverse): Users with appropriate permissions shall be able to void or reverse a committed import batch (all-or-nothing), requiring a typed confirmation phrase and audit reason.
 */

import { useState, useEffect } from 'react'

interface ImportBatch {
  batch_id: number
  file_name: string
  file_checksum: string
  source_type: string
  total_rows: number
  imported_rows: number
  quarantine_rows: number
  balance_result: string
  net_imbalance: number
  status: string
  created_at: string
}

interface ValidationCheck {
  check_code: string
  check_name: string
  status: string
  severity: string
  offending_count: number
  detail: string
}

interface QuarantineRow {
  row_index: number
  raw_data: string
  error_message: string
}

interface BatchDetailData extends ImportBatch {
  checks?: ValidationCheck[]
  quarantinedRows?: QuarantineRow[]
}

interface ImportHistoryScreenProps {
  sessionToken: string | null
}

export function ImportHistoryScreen({ sessionToken }: ImportHistoryScreenProps) {
  const [batches, setBatches] = useState<ImportBatch[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedBatch, setSelectedBatch] = useState<BatchDetailData | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Void Modal State
  const [voidingBatchId, setVoidingBatchId] = useState<number | null>(null)
  const [voidReason, setVoidReason] = useState('')
  const [confirmText, setConfirmText] = useState('')
  const [voidError, setVoidError] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 3500)
  }

  const fetchBatches = async () => {
    setLoading(true)
    setError(null)
    try {
      const headers: Record<string, string> = {}
      if (sessionToken) headers['Authorization'] = `Bearer ${sessionToken}`
      const res = await fetch('/api/v1/imports', { headers })
      const json = await res.json()
      if (json.status === 'ok' && json.data && json.data.items) {
        setBatches(json.data.items)
      } else {
        setError('Failed to load import batch history.')
      }
    } catch (err: any) {
      setError(err.message || 'Network error loading batches.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBatches()
  }, [sessionToken])

  const handleSelectBatch = async (batchId: number) => {
    setDetailLoading(true)
    try {
      const headers: Record<string, string> = {}
      if (sessionToken) headers['Authorization'] = `Bearer ${sessionToken}`
      const res = await fetch(`/api/v1/imports/${batchId}`, { headers })
      const json = await res.json()
      if (json.status === 'ok' && json.data) {
        setSelectedBatch(json.data)
      } else {
        showToast('Failed to load batch details.')
      }
    } catch (err: any) {
      showToast(err.message || 'Error loading batch details.')
    } finally {
      setDetailLoading(false)
    }
  }

  const handleVoidSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!voidingBatchId) return
    if (confirmText !== 'VOID') {
      setVoidError('You must type exactly "VOID" to confirm.')
      return
    }
    if (!voidReason.trim()) {
      setVoidError('An audit reason is required.')
      return
    }

    setVoidError(null)
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (sessionToken) headers['Authorization'] = `Bearer ${sessionToken}`
      const res = await fetch(`/api/v1/imports/${voidingBatchId}/void`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ confirm: true, reason: voidReason.trim() }),
      })
      const json = await res.json()
      if (res.ok && json.status === 'ok') {
        showToast(`Batch #${voidingBatchId} successfully voided.`)
        setVoidingBatchId(null)
        setVoidReason('')
        setConfirmText('')
        setSelectedBatch(null)
        fetchBatches()
      } else {
        setVoidError(json.detail || 'Failed to void batch.')
      }
    } catch (err: any) {
      setVoidError(err.message || 'Network error voiding batch.')
    }
  }

  return (
    <div style={{ maxWidth: '1300px', margin: '0 auto', padding: '16px' }}>
      {toastMessage && (
        <div style={{ position: 'fixed', bottom: '24px', right: '24px', backgroundColor: '#0f172a', color: '#f8fafc', padding: '12px 20px', borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', zIndex: 1000, fontSize: '13px', fontWeight: 500, borderLeft: '4px solid #38bdf8' }}>
          {toastMessage}
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 6px', fontSize: '20px', color: '#0f172a' }}>Import History & Batch Audit Log (FR-IMP-023)</h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
            Inspect historical import batches, cryptographic checksums, validation check reports, and perform all-or-nothing batch reversals (`FR-IMP-024`).
          </p>
        </div>
        <button
          onClick={fetchBatches}
          style={{ backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', padding: '8px 16px', borderRadius: '6px', fontWeight: 600, fontSize: '13px', cursor: 'pointer', color: '#334155' }}
        >
          🔄 Refresh History
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', marginBottom: '20px', fontSize: '13px', fontWeight: 600 }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading import batch history...</div>
      ) : batches.length === 0 ? (
        <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '40px', textAlign: 'center', color: '#64748b' }}>
          No import batches found. Use the Import Wizard to ingest datasets.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: selectedBatch ? '1fr 1.2fr' : '1fr', gap: '20px' }}>
          {/* Batches Table */}
          <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                  <th style={{ padding: '12px' }}>ID</th>
                  <th style={{ padding: '12px' }}>File Name</th>
                  <th style={{ padding: '12px' }}>Rows</th>
                  <th style={{ padding: '12px' }}>Balance</th>
                  <th style={{ padding: '12px' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {batches.map(b => (
                  <tr key={b.batch_id} style={{ borderBottom: '1px solid #f1f5f9', backgroundColor: selectedBatch?.batch_id === b.batch_id ? '#f0f9ff' : 'transparent' }}>
                    <td style={{ padding: '12px', fontWeight: 600, color: '#0284c7' }}>#{b.batch_id}</td>
                    <td style={{ padding: '12px', color: '#1e293b', fontWeight: 500 }}>
                      <div>{b.file_name}</div>
                      <div style={{ fontSize: '11px', color: '#64748b', fontFamily: 'monospace' }}>SHA: {b.file_checksum?.substring(0, 10)}...</div>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'monospace' }}>{b.imported_rows} / {b.total_rows}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, backgroundColor: b.balance_result === 'balanced' ? '#dcfce7' : '#fee2e2', color: b.balance_result === 'balanced' ? '#166534' : '#991b1b' }}>
                        {b.balance_result}
                      </span>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, backgroundColor: b.status === 'committed' ? '#dcfce7' : b.status === 'voided' ? '#fee2e2' : '#fef3c7', color: b.status === 'committed' ? '#166534' : b.status === 'voided' ? '#991b1b' : '#92400e' }}>
                        {b.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                        <button
                          onClick={() => handleSelectBatch(b.batch_id)}
                          style={{ padding: '4px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', backgroundColor: '#fff', color: '#0284c7', fontWeight: 600, fontSize: '12px', cursor: 'pointer' }}
                        >
                          Report
                        </button>
                        {b.status !== 'voided' && (
                          <button
                            onClick={() => setVoidingBatchId(b.batch_id)}
                            style={{ padding: '4px 10px', borderRadius: '4px', border: '1px solid #fca5a5', backgroundColor: '#fef2f2', color: '#991b1b', fontWeight: 600, fontSize: '12px', cursor: 'pointer' }}
                          >
                            Void
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Batch Detail & Validation Report Drawer */}
          {selectedBatch && (
            <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
                <div>
                  <h3 style={{ margin: '0 0 4px', fontSize: '16px', color: '#0f172a' }}>Batch #{selectedBatch.batch_id} Report</h3>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>{selectedBatch.file_name} • {selectedBatch.created_at}</div>
                </div>
                <button
                  onClick={() => setSelectedBatch(null)}
                  style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#64748b' }}
                >
                  ✕
                </button>
              </div>

              {detailLoading ? (
                <div style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>Loading batch inspection report...</div>
              ) : (
                <div style={{ display: 'grid', gap: '16px', fontSize: '13px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', backgroundColor: '#f8fafc', padding: '12px', borderRadius: '8px' }}>
                    <div><strong>Checksum:</strong> <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#475569' }}>{selectedBatch.file_checksum}</span></div>
                    <div><strong>Source Type:</strong> {selectedBatch.source_type}</div>
                    <div><strong>Total Rows:</strong> {selectedBatch.total_rows}</div>
                    <div><strong>Imported Rows:</strong> {selectedBatch.imported_rows}</div>
                    <div><strong>Quarantine Rows:</strong> {selectedBatch.quarantine_rows}</div>
                    <div><strong>Net Imbalance:</strong> ${selectedBatch.net_imbalance?.toLocaleString()}</div>
                  </div>

                  <div>
                    <h4 style={{ margin: '0 0 8px', fontSize: '14px', color: '#1e293b' }}>Validation Checks</h4>
                    {selectedBatch.checks && selectedBatch.checks.length > 0 ? (
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                        <thead>
                          <tr style={{ backgroundColor: '#f1f5f9', textAlign: 'left', color: '#475569' }}>
                            <th style={{ padding: '6px' }}>Code</th>
                            <th style={{ padding: '6px' }}>Name</th>
                            <th style={{ padding: '6px' }}>Status</th>
                            <th style={{ padding: '6px' }}>Detail</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedBatch.checks.map((chk, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                              <td style={{ padding: '6px', fontFamily: 'monospace', fontWeight: 600 }}>{chk.check_code}</td>
                              <td style={{ padding: '6px' }}>{chk.check_name}</td>
                              <td style={{ padding: '6px' }}>
                                <span style={{ padding: '1px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 600, backgroundColor: chk.status === 'passed' ? '#dcfce7' : '#fee2e2', color: chk.status === 'passed' ? '#166534' : '#991b1b' }}>
                                  {chk.status}
                                </span>
                              </td>
                              <td style={{ padding: '6px', color: '#64748b' }}>{chk.detail}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <div style={{ color: '#64748b', fontStyle: 'italic' }}>No validation checks recorded for this batch.</div>
                    )}
                  </div>

                  {selectedBatch.quarantinedRows && selectedBatch.quarantinedRows.length > 0 && (
                    <div>
                      <h4 style={{ margin: '0 0 8px', fontSize: '14px', color: '#1e293b' }}>Quarantined Rows ({selectedBatch.quarantinedRows.length})</h4>
                      <div style={{ maxHeight: '150px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '8px', backgroundColor: '#fff' }}>
                        {selectedBatch.quarantinedRows.map((q, idx) => (
                          <div key={idx} style={{ fontSize: '11px', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px', marginBottom: '4px' }}>
                            <span style={{ color: '#991b1b', fontWeight: 600 }}>Row {q.row_index}:</span> {q.error_message}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedBatch.status !== 'voided' && (
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
                      <button
                        onClick={() => setVoidingBatchId(selectedBatch.batch_id)}
                        style={{ backgroundColor: '#ef4444', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
                      >
                        Void / Reverse Batch #{selectedBatch.batch_id}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Void Confirmation Modal (FR-IMP-024) */}
      {voidingBatchId !== null && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 2000 }}>
          <div style={{ backgroundColor: '#fff', borderRadius: '12px', width: '480px', padding: '24px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '18px', color: '#991b1b' }}>⚠️ Void / Reverse Batch #{voidingBatchId}</h3>
            <p style={{ fontSize: '13px', color: '#475569', margin: '0 0 16px' }}>
              Voiding an import batch is an all-or-nothing operation (`FR-IMP-024`). It removes all transaction contributions from this batch and marks the batch as voided in the audit log.
            </p>

            {voidError && (
              <div style={{ padding: '10px 14px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', marginBottom: '16px', fontSize: '13px', fontWeight: 600 }}>
                {voidError}
              </div>
            )}

            <form onSubmit={handleVoidSubmit} style={{ display: 'grid', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Audit Reason for Reversal *</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Provide mandatory audit reason for voiding this import batch..."
                  value={voidReason}
                  onChange={e => setVoidReason(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>Type <strong>VOID</strong> to Confirm *</label>
                <input
                  type="text"
                  required
                  placeholder="Type VOID here"
                  value={confirmText}
                  onChange={e => setConfirmText(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => { setVoidingBatchId(null); setVoidReason(''); setConfirmText(''); setVoidError(null); }}
                  style={{ backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', padding: '8px 16px', borderRadius: '6px', fontWeight: 600, fontSize: '13px', cursor: 'pointer', color: '#334155' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ backgroundColor: '#ef4444', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
                >
                  Confirm Void Batch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

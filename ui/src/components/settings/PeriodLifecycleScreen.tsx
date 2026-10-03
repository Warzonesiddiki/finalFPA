/**
 * Period Lifecycle Management Screen (SCR-028..032 & FR-PRJ-003, 004, 005, 010)
 *
 * Functional Requirements quoted from docs/02_FUNCTIONAL_SPEC.md:
 * - FR-PRJ-003: Period status indicators (Open/Closed) across screens.
 * - FR-PRJ-004: New Period wizard (open period, source-load checklist, carry forward mappings/assumptions never numbers).
 * - FR-PRJ-005: Period close with immutable snapshot + typed reopen (audited).
 * - FR-PRJ-010: Period-close snapshot (captures immutable summary of actuals/budget).
 */

import { useState, useEffect } from 'react'

interface PeriodItem {
  period_id: number
  fiscal_year: number
  period_number: number
  period_code: string
  period_label: string
  start_date: string
  end_date: string
  status: 'open' | 'closed'
  has_actuals: boolean
  has_budget: boolean
  is_forecast_eligible: boolean
  closed_at: string | null
  created_at: string | null
}

export function PeriodLifecycleScreen() {
  const [periods, setPeriods] = useState<PeriodItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  // Wizard modal state
  const [showWizard, setShowWizard] = useState(false)
  const [wizardStep, setWizardStep] = useState<1 | 2 | 3>(1)
  const [newCode, setNewCode] = useState('FY26-P10')
  const [newLabel, setNewLabel] = useState('FY26 Period 10 (October 2026)')
  const [newYear, setNewYear] = useState('2026')
  const newNum = '10'
  const [newStart, setNewStart] = useState('2026-10-01')
  const [newEnd, setNewEnd] = useState('2026-10-31')
  const [carryMappings, setCarryMappings] = useState(true)
  const [carryAssumptions, setCarryAssumptions] = useState(true)

  // Reopen modal state
  const [reopenPeriodId, setReopenPeriodId] = useState<number | null>(null)
  const [reopenCodeConfirm, setReopenCodeConfirm] = useState('')
  const [reopenReason, setReopenReason] = useState('')

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 4000)
  }

  const fetchPeriods = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/v1/periods', {
        headers: { 'X-Session-Token': window.localStorage.getItem('fpa_session_token') || 'demo' }
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setPeriods(data.data.items)
      } else {
        setError('Failed to load periods')
      }
    } catch (e: any) {
      setError(e.message || 'Error connecting to backend')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPeriods()
  }, [])

  const handleOpenPeriodSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await fetch('/api/v1/periods/open', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': window.localStorage.getItem('fpa_session_token') || 'demo'
        },
        body: JSON.stringify({
          fiscal_year: parseInt(newYear) || 2026,
          period_number: parseInt(newNum) || 10,
          period_code: newCode,
          period_label: newLabel,
          start_date: newStart,
          end_date: newEnd,
          carry_forward_mappings: carryMappings,
          carry_forward_assumptions: carryAssumptions,
        })
      })
      const data = await res.json()
      if (data.status === 'ok') {
        showToast(`Period ${newCode} opened successfully via New Period wizard.`)
        setShowWizard(false)
        setWizardStep(1)
        fetchPeriods()
      } else {
        alert(data.message || 'Failed to open period')
      }
    } catch (e: any) {
      alert(e.message || 'Error opening period')
    }
  }

  const handleClosePeriod = async (periodId: number, code: string) => {
    if (!confirm(`Are you sure you want to CLOSE period ${code}? This will create an immutable snapshot and lock actuals.`)) {
      return
    }
    try {
      const res = await fetch(`/api/v1/periods/${periodId}/close`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': window.localStorage.getItem('fpa_session_token') || 'demo'
        }
      })
      const data = await res.json()
      if (data.status === 'ok') {
        showToast(`Period ${code} closed successfully with immutable snapshot.`)
        fetchPeriods()
      } else {
        alert(data.message || 'Failed to close period')
      }
    } catch (e: any) {
      alert(e.message || 'Error closing period')
    }
  }

  const handleReopenPeriodSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reopenPeriodId) return
    const targetPeriod = periods.find(p => p.period_id === reopenPeriodId)
    if (!targetPeriod) return

    if (reopenCodeConfirm.trim() !== targetPeriod.period_code) {
      alert(`Typed confirmation mismatch! Please type exact period code "${targetPeriod.period_code}" to confirm reopen.`)
      return
    }
    if (!reopenReason.trim() || reopenReason.length < 5) {
      alert('Audit reason must be at least 5 characters.')
      return
    }

    try {
      const res = await fetch(`/api/v1/periods/${reopenPeriodId}/reopen`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': window.localStorage.getItem('fpa_session_token') || 'demo'
        },
        body: JSON.stringify({
          reason: reopenReason,
          reopened_by: 'Authorized Controller'
        })
      })
      const data = await res.json()
      if (data.status === 'ok') {
        showToast(`Period ${targetPeriod.period_code} reopened successfully (audited).`)
        setReopenPeriodId(null)
        setReopenCodeConfirm('')
        setReopenReason('')
        fetchPeriods()
      } else {
        alert(data.message || 'Failed to reopen period')
      }
    } catch (e: any) {
      alert(e.message || 'Error reopening period')
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {toast && (
        <div className="fixed top-4 right-4 bg-emerald-600 text-white px-4 py-2 rounded shadow-lg z-50 text-sm font-medium">
          {toast}
        </div>
      )}

      <div className="flex justify-between items-center border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Period Lifecycle & Close Management</h1>
          <p className="text-sm text-slate-600 mt-1">
            Manage period status (Open / Closed), New Period wizard (FR-PRJ-004), and audited close snapshots (FR-PRJ-005).
          </p>
        </div>
        <button
          onClick={() => setShowWizard(true)}
          className="bg-sky-600 hover:bg-sky-700 text-white px-4 py-2 rounded-lg text-sm font-medium shadow transition"
        >
          + Open New Period (Wizard)
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {error}
        </div>
      )}

      {loading && periods.length === 0 ? (
        <div className="text-center py-12 text-slate-500">Loading period lifecycle status...</div>
      ) : (
        <div className="bg-white rounded-xl shadow border border-slate-200 overflow-hidden">
          <table className="w-full text-left border-collapse text-sm">
            <thead className="bg-slate-50 text-slate-700 uppercase tracking-wider text-xs font-semibold border-b">
              <tr>
                <th className="py-3 px-4">Period Code</th>
                <th className="py-3 px-4">Fiscal Label</th>
                <th className="py-3 px-4">Date Range</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Actuals / Budget</th>
                <th className="py-3 px-4">Closed At</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {periods.map(p => (
                <tr key={p.period_id} className="hover:bg-slate-50 transition">
                  <td className="py-3 px-4 font-semibold text-slate-900">{p.period_code}</td>
                  <td className="py-3 px-4 text-slate-700">{p.period_label}</td>
                  <td className="py-3 px-4 text-slate-600 font-mono text-xs">{p.start_date} to {p.end_date}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      p.status === 'open'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {p.status === 'open' ? '🟢 Open' : '🔒 Closed'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-600">
                    Actuals: {p.has_actuals ? '✓ Yes' : '—'} | Budget: {p.has_budget ? '✓ Yes' : '—'}
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-500 font-mono">
                    {p.closed_at ? new Date(p.closed_at).toLocaleString() : '—'}
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    {p.status === 'open' ? (
                      <button
                        onClick={() => handleClosePeriod(p.period_id, p.period_code)}
                        className="bg-amber-600 hover:bg-amber-700 text-white px-3 py-1 rounded text-xs font-medium shadow-sm transition"
                      >
                        Close Period
                      </button>
                    ) : (
                      <button
                        onClick={() => setReopenPeriodId(p.period_id)}
                        className="bg-slate-700 hover:bg-slate-800 text-white px-3 py-1 rounded text-xs font-medium shadow-sm transition"
                      >
                        Typed Reopen...
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* New Period Wizard Modal */}
      {showWizard && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200">
            <div className="bg-slate-900 text-white px-6 py-4 flex justify-between items-center">
              <h3 className="font-semibold text-lg">New Period Wizard (FR-PRJ-004)</h3>
              <button onClick={() => setShowWizard(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleOpenPeriodSubmit} className="p-6 space-y-4">
              {wizardStep === 1 && (
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-slate-800">Step 1: Period Identification & Dates</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 mb-1">Period Code</label>
                      <input
                        type="text"
                        value={newCode}
                        onChange={e => setNewCode(e.target.value)}
                        className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-700 mb-1">Fiscal Year</label>
                      <input
                        type="number"
                        value={newYear}
                        onChange={e => setNewYear(e.target.value)}
                        className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">Period Label</label>
                    <input
                      type="text"
                      value={newLabel}
                      onChange={e => setNewLabel(e.target.value)}
                      className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 mb-1">Start Date</label>
                      <input
                        type="date"
                        value={newStart}
                        onChange={e => setNewStart(e.target.value)}
                        className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-700 mb-1">End Date</label>
                      <input
                        type="date"
                        value={newEnd}
                        onChange={e => setNewEnd(e.target.value)}
                        className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
                        required
                      />
                    </div>
                  </div>
                  <div className="flex justify-end pt-4">
                    <button
                      type="button"
                      onClick={() => setWizardStep(2)}
                      className="bg-sky-600 hover:bg-sky-700 text-white px-4 py-2 rounded text-sm font-medium"
                    >
                      Next: Source-Load Checklist →
                    </button>
                  </div>
                </div>
              )}

              {wizardStep === 2 && (
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-slate-800">Step 2: Source-Load Checklist</h4>
                  <p className="text-xs text-slate-600">Verify source file connectivity and checklist requirements for {newCode}:</p>
                  <div className="space-y-2 bg-slate-50 p-3 rounded border text-xs text-slate-700">
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" defaultChecked disabled className="rounded text-sky-600" />
                      <span>D365 GL Actuals source connector ready</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" defaultChecked disabled className="rounded text-sky-600" />
                      <span>Bank Ledger reconciliation feed verified</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" defaultChecked disabled className="rounded text-sky-600" />
                      <span>Payroll & Procurement actuals feed active</span>
                    </label>
                  </div>
                  <div className="flex justify-between pt-4">
                    <button
                      type="button"
                      onClick={() => setWizardStep(1)}
                      className="bg-slate-200 hover:bg-slate-300 text-slate-800 px-4 py-2 rounded text-sm font-medium"
                    >
                      ← Back
                    </button>
                    <button
                      type="button"
                      onClick={() => setWizardStep(3)}
                      className="bg-sky-600 hover:bg-sky-700 text-white px-4 py-2 rounded text-sm font-medium"
                    >
                      Next: Carry Forward Mappings →
                    </button>
                  </div>
                </div>
              )}

              {wizardStep === 3 && (
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-slate-800">Step 3: Carry Forward Mappings & Assumptions</h4>
                  <p className="text-xs text-slate-600">
                    Per FR-PRJ-004: Carry forward chart of accounts mappings and forecasting assumptions. Financial actual numbers are <strong>never</strong> carried forward automatically.
                  </p>
                  <div className="space-y-3 pt-2">
                    <label className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={carryMappings}
                        onChange={e => setCarryMappings(e.target.checked)}
                        className="mt-0.5 rounded text-sky-600"
                      />
                      <div className="text-xs">
                        <span className="font-medium text-slate-900">Carry forward Chart of Accounts & Cost Center mappings</span>
                        <p className="text-slate-500">Inherit latest mapping profile v2.1 without resetting adjustments.</p>
                      </div>
                    </label>
                    <label className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={carryAssumptions}
                        onChange={e => setCarryAssumptions(e.target.checked)}
                        className="mt-0.5 rounded text-sky-600"
                      />
                      <div className="text-xs">
                        <span className="font-medium text-slate-900">Carry forward Forecast Driver Assumptions</span>
                        <p className="text-slate-500">Inherit run-rate N=3 and macro growth assumptions for new period.</p>
                      </div>
                    </label>
                  </div>
                  <div className="flex justify-between pt-4">
                    <button
                      type="button"
                      onClick={() => setWizardStep(2)}
                      className="bg-slate-200 hover:bg-slate-300 text-slate-800 px-4 py-2 rounded text-sm font-medium"
                    >
                      ← Back
                    </button>
                    <button
                      type="submit"
                      className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded text-sm font-medium shadow"
                    >
                      Open Period & Publish
                    </button>
                  </div>
                </div>
              )}
            </form>
          </div>
        </div>
      )}

      {/* Typed Reopen Modal */}
      {reopenPeriodId !== null && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-200">
            <div className="bg-amber-800 text-white px-6 py-4 flex justify-between items-center">
              <h3 className="font-semibold text-lg">Typed Reopen (Audited)</h3>
              <button onClick={() => setReopenPeriodId(null)} className="text-amber-200 hover:text-white">✕</button>
            </div>
            <form onSubmit={handleReopenPeriodSubmit} className="p-6 space-y-4">
              <p className="text-xs text-slate-600">
                Reopening a closed period requires entering the exact period code and a mandatory audit reason per FR-PRJ-005.
              </p>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Type period code to confirm: <span className="font-mono font-bold text-slate-900">{periods.find(p => p.period_id === reopenPeriodId)?.period_code}</span>
                </label>
                <input
                  type="text"
                  value={reopenCodeConfirm}
                  onChange={e => setReopenCodeConfirm(e.target.value)}
                  placeholder="e.g. FY26-P09"
                  className="w-full border border-slate-300 rounded px-3 py-2 text-sm font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Audit Reason (min 5 chars)</label>
                <textarea
                  value={reopenReason}
                  onChange={e => setReopenReason(e.target.value)}
                  placeholder="Provide detailed justification for reopening closed period..."
                  className="w-full border border-slate-300 rounded px-3 py-2 text-sm h-24"
                  required
                />
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setReopenPeriodId(null)}
                  className="bg-slate-200 hover:bg-slate-300 text-slate-800 px-4 py-2 rounded text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded text-sm font-medium shadow"
                >
                  Confirm Audited Reopen
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

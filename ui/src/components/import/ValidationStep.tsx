import React, { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle2, XCircle, ArrowLeft, ArrowRight, RefreshCw, ShieldAlert, SkipForward } from 'lucide-react'
import { FileItem, OffenderItem } from './types'

interface ValidationStepProps {
  file: FileItem
  onBack: () => void
  onNext: () => void
}

const STAGES = [
  { id: 'prescan', label: '1. Pre-scan & Boundaries' },
  { id: 'parse', label: '2. Delimiter & Header Parse' },
  { id: 'validate', label: '3. 32-Point Audit Rules' },
  { id: 'stage', label: '4. DuckDB Staging' },
  { id: 'commit', label: '5. Ready for Commit' },
]

export const ValidationStep: React.FC<ValidationStepProps> = ({
  file,
  onBack,
  onNext,
}) => {
  const [isRunning, setIsRunning] = useState(true)
  const [progress, setProgress] = useState(0)
  const [activeStageIdx, setActiveStageIdx] = useState(0)
  const [elapsedSec, setElapsedSec] = useState(0)
  const [isCancelled, setIsCancelled] = useState(false)
  const [activeTab, setActiveTab] = useState<'all' | 'errors' | 'quarantine' | 'warnings' | 'skipped'>('all')

  // Sample realistic offenders matching repository test rules (e.g., IMP-014 date format, IMP-021 zero amount)
  const [offenders] = useState<OffenderItem[]>([
    {
      code: 'IMP-014',
      name: 'Date values parsed without guessing',
      severity: 'quarantine',
      sheet: file.selectedSheet || 'Sheet1',
      row: 142,
      cell: 'B142',
      sampleValue: '31/02/2026',
      reason: 'Invalid calendar date 31/02/2026. Routed to quarantine review register.',
    },
    {
      code: 'IMP-014',
      name: 'Date values parsed without guessing',
      severity: 'quarantine',
      sheet: file.selectedSheet || 'Sheet1',
      row: 289,
      cell: 'B289',
      sampleValue: '99/99/9999',
      reason: 'Unparseable date value format. Routed to quarantine review register.',
    },
    {
      code: 'IMP-021',
      name: 'Zero-amount rows noted',
      severity: 'warning',
      sheet: file.selectedSheet || 'Sheet1',
      row: 53,
      cell: 'G53',
      sampleValue: '0.00 / 0.00',
      reason: 'Both debit and credit equal 0.00. Logged as zero-activity entry.',
    },
    {
      code: 'IMP-021',
      name: 'Zero-amount rows noted',
      severity: 'warning',
      sheet: file.selectedSheet || 'Sheet1',
      row: 88,
      cell: 'G88',
      sampleValue: '0.00 / 0.00',
      reason: 'Both debit and credit equal 0.00. Logged as zero-activity entry.',
    },
    {
      code: 'EXC-014',
      name: 'Vendor category master data cross-check',
      severity: 'skipped',
      reason: 'Vendor category master list not loaded for FY26. Check skipped with audit disclosure.',
    },
  ])

  // Simulated live execution timer
  useEffect(() => {
    if (!isRunning || isCancelled) return

    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          setIsRunning(false)
          clearInterval(interval)
          return 100
        }
        const next = Math.min(100, p + 18)
        if (next < 25) setActiveStageIdx(0)
        else if (next < 50) setActiveStageIdx(1)
        else if (next < 80) setActiveStageIdx(2)
        else if (next < 95) setActiveStageIdx(3)
        else setActiveStageIdx(4)
        return next
      })
      setElapsedSec(e => e + 1)
    }, 400)

    return () => clearInterval(interval)
  }, [isRunning, isCancelled])

  const handleCancel = () => {
    setIsCancelled(true)
    setIsRunning(false)
  }

  const handleRestart = () => {
    setIsCancelled(false)
    setIsRunning(true)
    setProgress(0)
    setElapsedSec(0)
    setActiveStageIdx(0)
  }

  const errorCount = offenders.filter(o => o.severity === 'error').length
  const quarantineCount = offenders.filter(o => o.severity === 'quarantine').length
  const warningCount = offenders.filter(o => o.severity === 'warning').length
  const skippedCount = offenders.filter(o => o.severity === 'skipped').length
  const passedCount = 28 // 32 checks total

  const filteredOffenders = offenders.filter(o => {
    if (activeTab === 'all') return true
    if (activeTab === 'errors') return o.severity === 'error'
    if (activeTab === 'quarantine') return o.severity === 'quarantine'
    if (activeTab === 'warnings') return o.severity === 'warning'
    if (activeTab === 'skipped') return o.severity === 'skipped'
    return true
  })

  const hasFatalErrors = errorCount > 0
  const canProceed = !isRunning && !isCancelled && !hasFatalErrors

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#0284c7', fontWeight: 700 }}>
          SCR-009 &bull; Step 5 of 6
        </span>
        <h2 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>
          Validation Progress &amp; Audit Results
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
          Real-time execution of the 32-check integrity harness (IMP-001..IMP-032). Failures are isolated to quarantine without silent discards.
        </p>
      </div>

      {/* Pipeline Stages & Progress Indicator Card */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {isRunning ? (
              <RefreshCw size={18} color="#0284c7" style={{ animation: 'spin 1.5s linear infinite' }} />
            ) : isCancelled ? (
              <XCircle size={18} color="#dc2626" />
            ) : (
              <CheckCircle2 size={18} color="#16a34a" />
            )}
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>
              {isRunning
                ? `Validating: ${STAGES[activeStageIdx].label}...`
                : isCancelled
                ? 'Validation Cancelled by Operator'
                : 'All 32 Validation Checks Complete'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px', color: '#64748b' }}>
            <span>Elapsed: <strong>{elapsedSec}s</strong></span>
            <span>ETA: <strong>{isRunning ? `${Math.max(0, 3 - elapsedSec)}s` : '0s'}</strong></span>
            {isRunning && (
              <button
                type="button"
                onClick={handleCancel}
                style={{
                  padding: '4px 10px',
                  backgroundColor: '#fee2e2',
                  color: '#991b1b',
                  border: '1px solid #fecaca',
                  borderRadius: '4px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: '12px',
                }}
              >
                Cancel Validation
              </button>
            )}
            {isCancelled && (
              <button
                type="button"
                onClick={handleRestart}
                style={{
                  padding: '4px 10px',
                  backgroundColor: '#e0f2fe',
                  color: '#0369a1',
                  border: '1px solid #bae6fd',
                  borderRadius: '4px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: '12px',
                }}
              >
                Restart Pipeline
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ height: '8px', backgroundColor: '#e2e8f0', borderRadius: '4px', overflow: 'hidden', marginBottom: '16px' }}>
          <div
            style={{
              height: '100%',
              width: `${progress}%`,
              backgroundColor: isCancelled ? '#dc2626' : progress === 100 ? '#16a34a' : '#0284c7',
              transition: 'width 0.3s ease',
            }}
          />
        </div>

        {/* Stage List Indicator */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', fontSize: '11px', textAlign: 'center' }}>
          {STAGES.map((s, idx) => {
            const isPassed = progress >= (idx + 1) * 20
            const isCurrent = activeStageIdx === idx && isRunning
            return (
              <div
                key={s.id}
                style={{
                  padding: '6px',
                  borderRadius: '4px',
                  backgroundColor: isPassed ? '#dcfce7' : isCurrent ? '#e0f2fe' : '#f8fafc',
                  color: isPassed ? '#166534' : isCurrent ? '#0369a1' : '#64748b',
                  fontWeight: isPassed || isCurrent ? 700 : 500,
                  border: isCurrent ? '1px solid #38bdf8' : '1px solid transparent',
                }}
              >
                {s.label}
              </div>
            )
          })}
        </div>
      </div>

      {/* Severity Counters Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        {/* Errors */}
        <div
          onClick={() => setActiveTab('errors')}
          style={{
            backgroundColor: '#ffffff',
            padding: '12px 16px',
            borderRadius: '8px',
            border: activeTab === 'errors' ? '2px solid #dc2626' : '1px solid #e2e8f0',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, color: '#dc2626' }}>
            <XCircle size={14} /> File Errors (Blocking)
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, marginTop: '4px', color: '#991b1b' }}>{errorCount}</div>
        </div>

        {/* Quarantine */}
        <div
          onClick={() => setActiveTab('quarantine')}
          style={{
            backgroundColor: '#ffffff',
            padding: '12px 16px',
            borderRadius: '8px',
            border: activeTab === 'quarantine' ? '2px solid #d97706' : '1px solid #e2e8f0',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, color: '#d97706' }}>
            <ShieldAlert size={14} /> Quarantined Rows
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, marginTop: '4px', color: '#b45309' }}>{quarantineCount}</div>
        </div>

        {/* Warnings */}
        <div
          onClick={() => setActiveTab('warnings')}
          style={{
            backgroundColor: '#ffffff',
            padding: '12px 16px',
            borderRadius: '8px',
            border: activeTab === 'warnings' ? '2px solid #0284c7' : '1px solid #e2e8f0',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, color: '#0284c7' }}>
            <AlertTriangle size={14} /> Warnings (Non-fatal)
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, marginTop: '4px', color: '#0369a1' }}>{warningCount}</div>
        </div>

        {/* Skipped */}
        <div
          onClick={() => setActiveTab('skipped')}
          style={{
            backgroundColor: '#ffffff',
            padding: '12px 16px',
            borderRadius: '8px',
            border: activeTab === 'skipped' ? '2px solid #64748b' : '1px solid #e2e8f0',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', textTransform: 'uppercase', fontWeight: 700, color: '#64748b' }}>
            <SkipForward size={14} /> Skipped Checks
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, marginTop: '4px', color: '#475569' }}>{skippedCount}</div>
        </div>
      </div>

      {/* Incremental Offenders Table */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', marginBottom: '24px' }}>
        <div style={{ padding: '12px 16px', backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>
            First Identified Offenders &amp; Rule Violations ({filteredOffenders.length})
          </div>
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            {passedCount} checks passed cleanly
          </span>
        </div>

        {filteredOffenders.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: '#16a34a', fontSize: '14px', fontWeight: 600 }}>
            ✓ No violations in this severity category.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                <th style={{ padding: '8px 14px' }}>Rule</th>
                <th style={{ padding: '8px 14px' }}>Severity</th>
                <th style={{ padding: '8px 14px' }}>Location</th>
                <th style={{ padding: '8px 14px' }}>Offending Value</th>
                <th style={{ padding: '8px 14px' }}>Audit Reason &amp; Disposition</th>
              </tr>
            </thead>
            <tbody>
              {filteredOffenders.map((off, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 14px', fontWeight: 700, color: '#0284c7' }}>
                    {off.code}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        backgroundColor:
                          off.severity === 'error'
                            ? '#fee2e2'
                            : off.severity === 'quarantine'
                            ? '#fef3c7'
                            : off.severity === 'warning'
                            ? '#e0f2fe'
                            : '#f1f5f9',
                        color:
                          off.severity === 'error'
                            ? '#991b1b'
                            : off.severity === 'quarantine'
                            ? '#92400e'
                            : off.severity === 'warning'
                            ? '#0369a1'
                            : '#475569',
                      }}
                    >
                      {off.severity}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: '#334155' }}>
                    {off.sheet ? `${off.sheet} : Row ${off.row} (${off.cell})` : '—'}
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: '#dc2626' }}>
                    {off.sampleValue || '—'}
                  </td>
                  <td style={{ padding: '10px 14px', color: '#475569' }}>
                    {off.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          type="button"
          onClick={onBack}
          disabled={isRunning}
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
            cursor: isRunning ? 'not-allowed' : 'pointer',
          }}
        >
          <ArrowLeft size={16} /> Back
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
          Commit &amp; Confirm Batch (SCR-010) <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}

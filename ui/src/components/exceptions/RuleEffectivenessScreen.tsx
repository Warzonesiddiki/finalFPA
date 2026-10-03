/**
 * Rule Effectiveness Analytics Dashboard & Tuning (doc 06 §9 & FR-EXC-015 / FR-SET-004)
 * 
 * Quoted from docs/06_EXCEPTION_RULES_CATALOG.md §9:
 * - Rule effectiveness analytics computed from FactExceptionEvent history:
 *   1. Times raised: Count of distinct identities ever raised.
 *   2. Explained / corrected share: Closures of type 'explained' or 'corrected' ÷ total closures (Signal that rule finds real issues).
 *   3. 'not_applicable' share: Closures of type 'not_applicable' ÷ total closures (Signal of false positives).
 *   4. Average days to close: Mean (closed_at − raised_at).
 *   5. Aging profile & Repeat rate.
 *   6. Last threshold tuning: Date and old→new of most recent threshold change.
 * - Review trigger: A rule with 'not_applicable' share above 'explained + corrected' share for two consecutive periods is flagged "review recommended" on the dashboard with the specific tuning path named. The engine improves month over month through configuration — never through hidden code changes.
 */

import { useState } from 'react'
import { ExceptionSeverityChart } from './ExceptionSeverityChart'
import { ExceptionAgingChart } from './ExceptionAgingChart'

interface RuleEffectivenessItem {
  ruleId: string
  ruleName: string
  timesRaised: number
  explainedCorrectedShare: number // %
  notApplicableShare: number // %
  avgDaysToClose: number
  repeatRate: number // %
  lastTuning: string
  consecutiveHighNaPeriods: number
  status: 'active' | 'review_recommended' | 'tuned'
  tuningPath: string
}

export function RuleEffectivenessScreen() {
  const [rules, setRules] = useState<RuleEffectivenessItem[]>([
    {
      ruleId: 'EXC-001',
      ruleName: 'Unapproved GL Journal Entry',
      timesRaised: 42,
      explainedCorrectedShare: 85.0,
      notApplicableShare: 15.0,
      avgDaysToClose: 3.2,
      repeatRate: 4.2,
      lastTuning: '2026-09-15 ($50k → $75k threshold)',
      consecutiveHighNaPeriods: 0,
      status: 'active',
      tuningPath: 'None (Stable)',
    },
    {
      ruleId: 'EXC-002',
      ruleName: 'Weekend Posting without Override',
      timesRaised: 128,
      explainedCorrectedShare: 35.0,
      notApplicableShare: 65.0,
      avgDaysToClose: 8.5,
      repeatRate: 18.3,
      lastTuning: '2026-08-10 (Added recurring weekend batch exclusion)',
      consecutiveHighNaPeriods: 2, // Triggers two-period review!
      status: 'review_recommended',
      tuningPath: 'Add subsidiary exclusion list or raise threshold to include automated payroll runs.',
    },
    {
      ruleId: 'EXC-003',
      ruleName: 'Duplicate Invoice Number Match',
      timesRaised: 18,
      explainedCorrectedShare: 94.0,
      notApplicableShare: 6.0,
      avgDaysToClose: 1.5,
      repeatRate: 0.0,
      lastTuning: '2026-09-01 (Strict 100% match)',
      consecutiveHighNaPeriods: 0,
      status: 'active',
      tuningPath: 'None (Optimal)',
    },
    {
      ruleId: 'EXC-004',
      ruleName: 'Budget Variance Exceeded',
      timesRaised: 64,
      explainedCorrectedShare: 78.0,
      notApplicableShare: 22.0,
      avgDaysToClose: 4.8,
      repeatRate: 6.1,
      lastTuning: '2026-09-20 (Variance % >15% & >$10k)',
      consecutiveHighNaPeriods: 0,
      status: 'active',
      tuningPath: 'None',
    },
    {
      ruleId: 'EXC-011',
      ruleName: 'Future-Dated Journal Entry',
      timesRaised: 215,
      explainedCorrectedShare: 41.0,
      notApplicableShare: 59.0,
      avgDaysToClose: 6.2,
      repeatRate: 24.5,
      lastTuning: '2026-09-25 (Period-end ranking mitigation added)',
      consecutiveHighNaPeriods: 2, // Triggers two-period review!
      status: 'review_recommended',
      tuningPath: 'Refine as_of default resolution to period end or adjust future threshold window.',
    },
  ])

  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null)
  const [newThreshold, setNewThreshold] = useState('')

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 3500)
  }

  const handleTuneRule = (ruleId: string) => {
    if (!newThreshold.trim()) return
    setRules(rules.map(r => r.ruleId === ruleId ? { ...r, lastTuning: `2026-10-02 (${newThreshold.trim()})`, status: 'tuned', consecutiveHighNaPeriods: 0, tuningPath: 'Tuned successfully' } : r))
    setEditingRuleId(null)
    setNewThreshold('')
    showToast(`Rule ${ruleId} tuned successfully via configuration (no code change).`)
  }

  return (
    <div style={{ maxWidth: '1300px', margin: '0 auto', display: 'grid', gap: '24px' }}>
      {toastMessage && (
        <div style={{ position: 'fixed', bottom: '24px', right: '24px', backgroundColor: '#0f172a', color: '#f8fafc', padding: '12px 20px', borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', zIndex: 1000, fontSize: '13px', fontWeight: 500, borderLeft: '4px solid #38bdf8' }}>
          {toastMessage}
        </div>
      )}

      {/* Header Banner */}
      <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <h2 style={{ margin: '0 0 6px', fontSize: '20px', color: '#0f172a' }}>Rule Effectiveness Analytics & Tuning Dashboard (Doc 06 §9)</h2>
        <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
          Monitor false-positive ratios, resolution velocity, and threshold effectiveness. Rules with <code style={{ backgroundColor: '#f1f5f9', padding: '2px 4px', borderRadius: '4px' }}>not_applicable &gt; explained + corrected</code> for two consecutive periods trigger automatic review recommendations.
        </p>
      </div>

      {/* Analytics Table */}
      <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontWeight: 600, fontSize: '14px', color: '#1e293b' }}>Exception Rule Performance Metrics</div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Engine improvements via configuration only (FR-SET-004)</div>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#475569' }}>
              <th style={{ padding: '12px' }}>Rule ID & Name</th>
              <th style={{ padding: '12px' }}>Times Raised</th>
              <th style={{ padding: '12px' }}>Explained / Corrected %</th>
              <th style={{ padding: '12px' }}>Not Applicable % (FP)</th>
              <th style={{ padding: '12px' }}>Avg Days to Close</th>
              <th style={{ padding: '12px' }}>Status / Review Trigger</th>
              <th style={{ padding: '12px', textAlign: 'right' }}>Configuration / Tune</th>
            </tr>
          </thead>
          <tbody>
            {rules.map(r => (
              <tr key={r.ruleId} style={{ borderBottom: '1px solid #f1f5f9', backgroundColor: r.status === 'review_recommended' ? '#fef2f2' : 'transparent' }}>
                <td style={{ padding: '12px' }}>
                  <div style={{ fontWeight: 600, color: '#0284c7', fontFamily: 'monospace' }}>{r.ruleId}</div>
                  <div style={{ color: '#1e293b', fontWeight: 500, fontSize: '12px' }}>{r.ruleName}</div>
                </td>
                <td style={{ padding: '12px', fontFamily: 'monospace', fontWeight: 600 }}>{r.timesRaised}</td>
                <td style={{ padding: '12px', fontFamily: 'monospace', color: '#166534', fontWeight: 600 }}>{r.explainedCorrectedShare}%</td>
                <td style={{ padding: '12px', fontFamily: 'monospace', color: r.notApplicableShare > 50 ? '#991b1b' : '#334155', fontWeight: 600 }}>
                  {r.notApplicableShare}%
                </td>
                <td style={{ padding: '12px', fontFamily: 'monospace' }}>{r.avgDaysToClose} days</td>
                <td style={{ padding: '12px' }}>
                  {r.status === 'review_recommended' ? (
                    <div>
                      <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, backgroundColor: '#fee2e2', color: '#991b1b' }}>
                        ⚠️ Review Recommended (2+ periods NA &gt; Valid)
                      </span>
                      <div style={{ fontSize: '11px', color: '#7f1d1d', marginTop: '4px' }}>Path: {r.tuningPath}</div>
                    </div>
                  ) : (
                    <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, backgroundColor: '#dcfce7', color: '#166534' }}>
                      Active &amp; Stable
                    </span>
                  )}
                </td>
                <td style={{ padding: '12px', textAlign: 'right' }}>
                  {editingRuleId === r.ruleId ? (
                    <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end', alignItems: 'center' }}>
                      <input
                        type="text"
                        placeholder="New threshold..."
                        value={newThreshold}
                        onChange={e => setNewThreshold(e.target.value)}
                        style={{ padding: '6px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', width: '140px' }}
                      />
                      <button
                        onClick={() => handleTuneRule(r.ruleId)}
                        style={{ backgroundColor: '#0284c7', color: '#fff', border: 'none', padding: '6px 10px', borderRadius: '4px', fontWeight: 600, fontSize: '11px', cursor: 'pointer' }}
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingRuleId(null)}
                        style={{ backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', padding: '6px 8px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setEditingRuleId(r.ruleId)}
                      style={{ padding: '5px 12px', borderRadius: '4px', border: '1px solid #cbd5e1', backgroundColor: '#fff', color: '#0f172a', fontWeight: 600, fontSize: '12px', cursor: 'pointer' }}
                    >
                      Tune Threshold
                    </button>
                  )}
                  <div style={{ fontSize: '10px', color: '#64748b', marginTop: '4px' }}>Last: {r.lastTuning}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Charts Batch 2: CHT-008 Severity Mix & CHT-010 Aging Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <ExceptionSeverityChart
          items={[
            { period: 'FY26-P07', critical: 12, warning: 28, info: 15 },
            { period: 'FY26-P08', critical: 8, warning: 34, info: 22 },
            { period: 'FY26-P09', critical: 15, warning: 24, info: 18 },
          ]}
        />
        <ExceptionAgingChart
          items={[
            { bucket: '0–7', count: 32 },
            { bucket: '8–30', count: 18 },
            { bucket: '31+', count: 7 },
          ]}
        />
      </div>
    </div>
  )
}

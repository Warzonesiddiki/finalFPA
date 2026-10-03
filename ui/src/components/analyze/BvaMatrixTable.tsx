import React from 'react'
import { BvaItem } from './types'

interface BvaMatrixTableProps {
  items: BvaItem[]
  isLoading: boolean
  onSelectRow: (item: BvaItem) => void
  onExportCsv: () => void
  onNavigateToImport?: () => void
}

export const BvaMatrixTable: React.FC<BvaMatrixTableProps> = ({
  items,
  isLoading,
  onSelectRow,
  onExportCsv,
  onNavigateToImport,
}) => {
  if (isLoading) {
    return (
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '36px', textAlign: 'center', color: '#64748b' }}>
        <div style={{ fontSize: '15px', fontWeight: 600, marginBottom: '6px' }}>Querying DuckDB Analytical Store...</div>
        <div style={{ fontSize: '13px' }}>Executing parameterized aggregations for Budget vs Actual variance matrix</div>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '40px 24px', textAlign: 'center' }}>
        <div style={{ fontSize: '16px', fontWeight: 700, color: '#1e293b', marginBottom: '8px' }}>
          No BvA Data Available (FR-BVA-016)
        </div>
        <p style={{ color: '#64748b', fontSize: '13px', maxWidth: '520px', margin: '0 auto 20px' }}>
          No transactional facts or budget entries found matching your active filters. Import actual transactions or budget files to view deterministic variance analysis.
        </p>
        {onNavigateToImport && (
          <button
            type="button"
            onClick={onNavigateToImport}
            style={{
              padding: '9px 18px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              borderRadius: '6px',
              border: 'none',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            ⬇ Go to Import Wizard
          </button>
        )}
      </div>
    )
  }

  // Calculate totals
  const totalActual = items.reduce((sum, it) => sum + Number(it.actualAmount || 0), 0)
  const totalBudget = items.reduce((sum, it) => sum + Number(it.budgetAmount || 0), 0)
  const totalVariance = totalActual - totalBudget
  const totalVariancePct = totalBudget !== 0 ? ((totalVariance / Math.abs(totalBudget)) * 100).toFixed(2) : null

  return (
    <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
      {/* Table Action Header */}
      <div style={{ padding: '14px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#f8fafc' }}>
        <div>
          <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
            Budget vs Actual Matrix (SCR-015 / FR-BVA-001)
          </span>
          <span style={{ marginLeft: '10px', fontSize: '12px', color: '#64748b' }}>
            {items.length} accounts &bull; Click any row to drill into source transactions
          </span>
        </div>
        <div>
          <button
            type="button"
            onClick={onExportCsv}
            style={{
              padding: '6px 14px',
              backgroundColor: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 600,
              color: '#334155',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>⭳</span> Export What You See (FR-BVA-011)
          </button>
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Statement Line</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Account</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Type</th>
              <th style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600 }}>Actual (₹)</th>
              <th style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600 }}>Budget (₹)</th>
              <th style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600 }}>Variance (₹)</th>
              <th style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600 }}>Var %</th>
              <th style={{ padding: '10px 14px', fontWeight: 600, textAlign: 'center' }}>Fav? (FR-BVA-003)</th>
              <th style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 600 }}>Evidence</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => {
              const actualNum = Number(item.actualAmount)
              const budgetNum = Number(item.budgetAmount)
              const varNum = Number(item.varianceAmount)
              const isFav = item.favourability === 'favourable'
              const isAdv = item.favourability === 'unfavourable'

              const badgeBg = isFav ? '#dcfce7' : isAdv ? '#fee2e2' : '#f1f5f9'
              const badgeColor = isFav ? '#15803d' : isAdv ? '#b91c1c' : '#475569'
              const badgeText = isFav ? 'Fav ▲' : isAdv ? 'Adv ▼' : '—'

              return (
                <tr
                  key={item.accountId}
                  onClick={() => onSelectRow(item)}
                  style={{
                    borderBottom: '1px solid #f1f5f9',
                    cursor: 'pointer',
                    transition: 'background-color 0.1s ease',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#f8fafc')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <td style={{ padding: '10px 14px', fontWeight: 500, color: '#334155' }}>
                    {item.statementLine}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontWeight: 600, color: '#0284c7' }}>{item.accountCode}</div>
                    <div style={{ fontSize: '12px', color: '#64748b' }}>{item.accountName}</div>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ fontSize: '11px', textTransform: 'capitalize', padding: '2px 6px', backgroundColor: '#f1f5f9', borderRadius: '4px', color: '#475569' }}>
                      {item.accountType}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600 }}>
                    ₹{actualNum.toLocaleString()}
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'right', color: budgetNum === 0 ? '#94a3b8' : '#0f172a' }}>
                    {budgetNum === 0 ? '—' : `₹${budgetNum.toLocaleString()}`}
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 700, color: badgeColor }}>
                    {varNum >= 0 ? `+₹${varNum.toLocaleString()}` : `-₹${Math.abs(varNum).toLocaleString()}`}
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'right', color: item.variancePct ? '#0f172a' : '#94a3b8' }}>
                    {item.variancePct ? `${Number(item.variancePct) >= 0 ? '+' : ''}${item.variancePct}%` : 'n/a'}
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: badgeBg,
                        color: badgeColor,
                      }}
                    >
                      {badgeText}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#0284c7', fontWeight: 600, textDecoration: 'underline' }}>
                      Drill ▸
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
          {/* Summary Footer Row */}
          <tfoot>
            <tr style={{ backgroundColor: '#f8fafc', borderTop: '2px solid #cbd5e1', fontWeight: 700 }}>
              <td style={{ padding: '12px 14px', color: '#0f172a' }} colSpan={3}>
                Totals ({items.length} accounts)
              </td>
              <td style={{ padding: '12px 14px', textAlign: 'right', color: '#0f172a' }}>
                ₹{totalActual.toLocaleString()}
              </td>
              <td style={{ padding: '12px 14px', textAlign: 'right', color: '#0f172a' }}>
                ₹{totalBudget.toLocaleString()}
              </td>
              <td style={{ padding: '12px 14px', textAlign: 'right', color: totalVariance >= 0 ? '#15803d' : '#b91c1c' }}>
                {totalVariance >= 0 ? `+₹${totalVariance.toLocaleString()}` : `-₹${Math.abs(totalVariance).toLocaleString()}`}
              </td>
              <td style={{ padding: '12px 14px', textAlign: 'right', color: '#0f172a' }}>
                {totalVariancePct ? `${Number(totalVariancePct) >= 0 ? '+' : ''}${totalVariancePct}%` : '—'}
              </td>
              <td style={{ padding: '12px 14px', textAlign: 'center' }} colSpan={2}>
                <span style={{ fontSize: '11px', color: '#64748b' }}>Exact Tie Invariant</span>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}

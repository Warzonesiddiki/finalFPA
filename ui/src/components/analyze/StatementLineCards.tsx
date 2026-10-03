import React from 'react'
import { StatementLineSummary } from './types'

interface StatementLineCardsProps {
  summaries: StatementLineSummary[]
  activeStatementLine: string | null
  onSelectStatementLine: (line: string | null) => void
}

export const StatementLineCards: React.FC<StatementLineCardsProps> = ({
  summaries,
  activeStatementLine,
  onSelectStatementLine,
}) => {
  if (summaries.length === 0) return null

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: '#334155' }}>
          Statement Line Rollups &bull; Tie-to-children Guarantee (FR-BVA-009)
        </div>
        {activeStatementLine && (
          <button
            type="button"
            onClick={() => onSelectStatementLine(null)}
            style={{
              padding: '3px 8px',
              fontSize: '11px',
              backgroundColor: '#fee2e2',
              color: '#991b1b',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            ✕ Clear Filter ({activeStatementLine})
          </button>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
        {summaries.map(s => {
          const isSelected = activeStatementLine === s.statementLine
          const actualNum = Number(s.actualAmount)
          const budgetNum = Number(s.budgetAmount)
          const varNum = Number(s.varianceAmount)
          const isFav = s.favourability === 'favourable'
          const isAdv = s.favourability === 'unfavourable'

          const badgeBg = isFav ? '#dcfce7' : isAdv ? '#fee2e2' : '#f1f5f9'
          const badgeColor = isFav ? '#15803d' : isAdv ? '#b91c1c' : '#475569'
          const badgeText = isFav ? 'Fav ▲' : isAdv ? 'Adv ▼' : '—'

          return (
            <div
              key={s.statementLine}
              onClick={() => onSelectStatementLine(isSelected ? null : s.statementLine)}
              style={{
                backgroundColor: isSelected ? '#f0f9ff' : '#ffffff',
                border: isSelected ? '2px solid #0284c7' : '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '14px',
                cursor: 'pointer',
                transition: 'all 0.15s ease-in-out',
                boxShadow: isSelected ? '0 2px 6px rgba(2, 132, 199, 0.12)' : 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                  {s.statementLine}
                </span>
                <span
                  style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 700,
                    backgroundColor: badgeBg,
                    color: badgeColor,
                  }}
                >
                  {badgeText}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '12px', marginBottom: '8px' }}>
                <div>
                  <span style={{ color: '#64748b' }}>Actual: </span>
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>₹{actualNum.toLocaleString()}</span>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Budget: </span>
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>₹{budgetNum.toLocaleString()}</span>
                </div>
              </div>

              <div style={{ borderTop: '1px dashed #e2e8f0', paddingTop: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                <span style={{ color: '#64748b' }}>Variance:</span>
                <span style={{ fontWeight: 700, color: badgeColor }}>
                  {varNum >= 0 ? `+₹${varNum.toLocaleString()}` : `-₹${Math.abs(varNum).toLocaleString()}`}
                  {s.variancePct ? ` (${s.variancePct}%)` : ''}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

import React from 'react'
import { FilterState } from './types'

interface BvaFilterBarProps {
  filters: FilterState
  availableStatementLines: string[]
  onFilterChange: (newFilters: Partial<FilterState>) => void
  onResetFilters: () => void
  onRefresh: () => void
  isLoading: boolean
}

const PERIODS = [
  { id: null, label: 'All Periods' },
  { id: 1, label: 'FY26-P01 (Jan-26)' },
  { id: 2, label: 'FY26-P02 (Feb-26)' },
  { id: 3, label: 'FY26-P03 (Mar-26)' },
  { id: 4, label: 'FY26-P04 (Apr-26)' },
  { id: 5, label: 'FY26-P05 (May-26)' },
  { id: 6, label: 'FY26-P06 (Jun-26)' },
  { id: 7, label: 'FY26-P07 (Jul-26)' },
  { id: 8, label: 'FY26-P08 (Aug-26)' },
  { id: 9, label: 'FY26-P09 (Sep-26)' },
  { id: 10, label: 'FY26-P10 (Oct-26)' },
  { id: 11, label: 'FY26-P11 (Nov-26)' },
  { id: 12, label: 'FY26-P12 (Dec-26)' },
]

export const BvaFilterBar: React.FC<BvaFilterBarProps> = ({
  filters,
  availableStatementLines,
  onFilterChange,
  onResetFilters,
  onRefresh,
  isLoading,
}) => {
  return (
    <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', marginBottom: '20px' }}>
      {/* Top Filter Controls */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', alignItems: 'flex-end' }}>
          {/* Period Selector (FR-BVA-002) */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Period (FR-BVA-002)
            </label>
            <select
              value={filters.periodId === null ? '' : filters.periodId}
              onChange={e => onFilterChange({ periodId: e.target.value === '' ? null : Number(e.target.value) })}
              style={{
                padding: '7px 10px',
                fontSize: '13px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                backgroundColor: '#f8fafc',
                color: '#0f172a',
                cursor: 'pointer',
              }}
            >
              {PERIODS.map(p => (
                <option key={p.id ?? 'all'} value={p.id ?? ''}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* Window Selector (FR-BVA-002) */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Window (FR-BVA-002)
            </label>
            <div style={{ display: 'flex', border: '1px solid #cbd5e1', borderRadius: '6px', overflow: 'hidden' }}>
              <button
                type="button"
                onClick={() => onFilterChange({ window: 'MTD' })}
                style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  border: 'none',
                  backgroundColor: filters.window === 'MTD' ? '#0284c7' : '#f8fafc',
                  color: filters.window === 'MTD' ? '#ffffff' : '#475569',
                  cursor: 'pointer',
                }}
              >
                MTD
              </button>
              <button
                type="button"
                onClick={() => onFilterChange({ window: 'YTD' })}
                style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  border: 'none',
                  borderLeft: '1px solid #cbd5e1',
                  backgroundColor: filters.window === 'YTD' ? '#0284c7' : '#f8fafc',
                  color: filters.window === 'YTD' ? '#ffffff' : '#475569',
                  cursor: 'pointer',
                }}
              >
                YTD
              </button>
            </div>
          </div>

          {/* Statement Line Filter (FR-BVA-009) */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Statement Line
            </label>
            <select
              value={filters.statementLine ?? ''}
              onChange={e => onFilterChange({ statementLine: e.target.value === '' ? null : e.target.value })}
              style={{
                padding: '7px 10px',
                fontSize: '13px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                backgroundColor: '#f8fafc',
                color: '#0f172a',
                cursor: 'pointer',
              }}
            >
              <option value="">All Statement Lines</option>
              {availableStatementLines.map(line => (
                <option key={line} value={line}>
                  {line}
                </option>
              ))}
            </select>
          </div>

          {/* Quick Search */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Search Accounts
            </label>
            <input
              type="text"
              placeholder="Code or name..."
              value={filters.searchQuery}
              onChange={e => onFilterChange({ searchQuery: e.target.value })}
              style={{
                padding: '7px 10px',
                fontSize: '13px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                backgroundColor: '#f8fafc',
                color: '#0f172a',
                width: '180px',
              }}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            type="button"
            onClick={onResetFilters}
            style={{
              padding: '7px 12px',
              fontSize: '12px',
              fontWeight: 500,
              backgroundColor: '#f1f5f9',
              color: '#475569',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            Reset Filters
          </button>
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
            style={{
              padding: '7px 14px',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              cursor: isLoading ? 'wait' : 'pointer',
              opacity: isLoading ? 0.7 : 1,
            }}
          >
            {isLoading ? 'Refreshing...' : '↻ Refresh Facts'}
          </button>
        </div>
      </div>

      {/* Disclosures Bar (FR-BVA-013 & FR-BVA-014) */}
      <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: '#64748b' }}>
        <div>
          <span style={{ fontWeight: 600, color: '#0369a1' }}>Comparability Guard (FR-BVA-013):</span> Comparing at: month &times; account &times; cost centre &bull; Budget available at: month &times; account
        </div>
        <div>
          <span style={{ padding: '2px 6px', backgroundColor: '#e2e8f0', borderRadius: '4px', fontWeight: 600, color: '#334155' }}>
            FR-BVA-014: Simple sum &mdash; no eliminations
          </span>
        </div>
      </div>
    </div>
  )
}

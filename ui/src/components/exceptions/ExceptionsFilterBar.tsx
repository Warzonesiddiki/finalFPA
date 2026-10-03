import React from 'react';
import { ExceptionFilterState, ExceptionsRegisterSummary } from './types';

interface ExceptionsFilterBarProps {
  filters: ExceptionFilterState;
  summary: ExceptionsRegisterSummary;
  onFilterChange: (filters: ExceptionFilterState) => void;
  onRunRules: () => void;
  isRunningRules: boolean;
  onExport: () => void;
  onCopyOwnerSummary: () => void;
}

export const ExceptionsFilterBar: React.FC<ExceptionsFilterBarProps> = ({
  filters,
  summary,
  onFilterChange,
  onRunRules,
  isRunningRules,
  onExport,
  onCopyOwnerSummary,
}) => {
  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '16px',
      }}
    >
      {/* Header Row: Title, KPI strip, and Top Action buttons per SCR-023 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          marginBottom: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>
              Exceptions Register &bull; {filters.period}
            </h2>
            <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '13px' }}>
              <span style={{ color: '#475569' }}>
                <strong style={{ color: '#0f172a' }}>{summary.total}</strong> total
              </span>
              <span style={{ color: '#475569' }}>&bull;</span>
              <span style={{ color: '#dc2626', fontWeight: 600 }}>
                {summary.open} open
              </span>
              <span style={{ color: '#475569' }}>&bull;</span>
              <span style={{ color: summary.overdue > 0 ? '#b91c1c' : '#475569', fontWeight: summary.overdue > 0 ? 700 : 500 }}>
                {summary.overdue} overdue
              </span>
              <span style={{ color: '#475569' }}>&bull;</span>
              <span style={{ color: '#991b1b', fontWeight: 600 }}>
                {summary.high} high severity
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={onCopyOwnerSummary}
            style={{
              padding: '8px 12px',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: '#f1f5f9',
              color: '#334155',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
            title="Copy plain-text summary grouped by owner for chat/email per FR-EXC-017"
          >
            📋 Copy Owner Summary
          </button>

          <button
            onClick={onExport}
            style={{
              padding: '8px 12px',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: '#f1f5f9',
              color: '#334155',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
            title="Export register to CSV/Excel per FR-EXC-018"
          >
            ⬇ Export Register
          </button>

          <button
            onClick={onRunRules}
            disabled={isRunningRules}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: 600,
              backgroundColor: isRunningRules ? '#94a3b8' : '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              cursor: isRunningRules ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {isRunningRules ? '⏳ Evaluating...' : '▶ Run Rules'}
          </button>
        </div>
      </div>

      {/* Filter Controls Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '12px',
          alignItems: 'flex-end',
        }}
      >
        {/* Severity */}
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>
            Severity
          </label>
          <select
            value={filters.severity}
            onChange={(e) => onFilterChange({ ...filters, severity: e.target.value })}
            style={{
              width: '100%',
              padding: '6px 8px',
              borderRadius: '4px',
              border: '1px solid #cbd5e1',
              fontSize: '12px',
              backgroundColor: '#fff',
            }}
          >
            <option value="All">All Severities</option>
            <option value="High">High ⚠</option>
            <option value="Medium">Medium ⚑</option>
            <option value="Low">Low ⓘ</option>
          </select>
        </div>

        {/* Status */}
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>
            Status
          </label>
          <select
            value={filters.status}
            onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
            style={{
              width: '100%',
              padding: '6px 8px',
              borderRadius: '4px',
              border: '1px solid #cbd5e1',
              fontSize: '12px',
              backgroundColor: '#fff',
            }}
          >
            <option value="All">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_review">In Review</option>
            <option value="explained">Explained</option>
            <option value="corrected">Corrected</option>
            <option value="closed">Closed</option>
            <option value="reopened">Reopened</option>
            <option value="not_applicable">Not Applicable</option>
          </select>
        </div>

        {/* Owner */}
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>
            Owner
          </label>
          <select
            value={filters.owner}
            onChange={(e) => onFilterChange({ ...filters, owner: e.target.value })}
            style={{
              width: '100%',
              padding: '6px 8px',
              borderRadius: '4px',
              border: '1px solid #cbd5e1',
              fontSize: '12px',
              backgroundColor: '#fff',
            }}
          >
            <option value="All">All Owners</option>
            <option value="Unassigned">Unassigned (FR-EXC-007)</option>
            <option value="Rahul">Rahul</option>
            <option value="Aarti">Aarti</option>
            <option value="Priya">Priya</option>
            <option value="Sanjay">Sanjay</option>
          </select>
        </div>

        {/* Aging Bucket */}
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>
            Aging Bucket
          </label>
          <select
            value={filters.agingBucket}
            onChange={(e) => onFilterChange({ ...filters, agingBucket: e.target.value })}
            style={{
              width: '100%',
              padding: '6px 8px',
              borderRadius: '4px',
              border: '1px solid #cbd5e1',
              fontSize: '12px',
              backgroundColor: '#fff',
            }}
          >
            <option value="all">All Buckets</option>
            <option value="0-7">0–7 days</option>
            <option value="8-30">8–30 days</option>
            <option value="31+">31+ days</option>
          </select>
        </div>

        {/* Rule Filter */}
        <div>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>
            Rule ID
          </label>
          <select
            value={filters.ruleId}
            onChange={(e) => onFilterChange({ ...filters, ruleId: e.target.value })}
            style={{
              width: '100%',
              padding: '6px 8px',
              borderRadius: '4px',
              border: '1px solid #cbd5e1',
              fontSize: '12px',
              backgroundColor: '#fff',
            }}
          >
            <option value="All">All Rules</option>
            <option value="EXC-001">EXC-001 Duplicate invoice candidate</option>
            <option value="EXC-002">EXC-002 Unmapped GL account</option>
            <option value="EXC-003">EXC-003 Inactive cost centre</option>
            <option value="EXC-004">EXC-004 Posting date mismatch</option>
            <option value="EXC-005">EXC-005 Negative expense / credit</option>
            <option value="EXC-006">EXC-006 Missing recurring cost</option>
            <option value="EXC-007">EXC-007 Material unbudgeted spend</option>
            <option value="EXC-008">EXC-008 Material variance</option>
            <option value="EXC-009">EXC-009 Fiscal period mismatch</option>
            <option value="EXC-010">EXC-010 Potential cut-off issue</option>
            <option value="EXC-011">EXC-011 Future-dated posting</option>
            <option value="EXC-012">EXC-012 Negative expense credit</option>
            <option value="EXC-013">EXC-013 Spike vs trailing average</option>
            <option value="EXC-014">EXC-014 Unusual vendor-account</option>
            <option value="EXC-015">EXC-015 Missing recurring cost</option>
            <option value="EXC-016">EXC-016 Missing expected accrual</option>
          </select>
        </div>

        {/* Free text search */}
        <div style={{ gridColumn: 'span 2' }}>
          <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>
            Search Subject or Hash
          </label>
          <input
            type="text"
            placeholder="Search voucher, vendor, account, or rule..."
            value={filters.search}
            onChange={(e) => onFilterChange({ ...filters, search: e.target.value })}
            style={{
              width: '100%',
              padding: '6px 10px',
              borderRadius: '4px',
              border: '1px solid #cbd5e1',
              fontSize: '12px',
            }}
          />
        </div>
      </div>
    </div>
  );
};

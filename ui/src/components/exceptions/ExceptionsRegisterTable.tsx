import React from 'react';
import { ExceptionItem } from './types';
import { tokens } from '../../theme/tokens';

interface ExceptionsRegisterTableProps {
  items: ExceptionItem[];
  selectedIds: number[];
  onSelectRow: (id: number, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onRowClick: (item: ExceptionItem) => void;
}

export const ExceptionsRegisterTable: React.FC<ExceptionsRegisterTableProps> = ({
  items,
  selectedIds,
  onSelectRow,
  onSelectAll,
  onRowClick,
}) => {
  const allSelected = items.length > 0 && items.every((it) => selectedIds.includes(it.exception_id));
  const someSelected = selectedIds.length > 0 && !allSelected;

  const formatCurrency = (val: string | number) => {
    const num = typeof val === 'string' ? parseFloat(val) : val;
    if (isNaN(num)) return '₹ 0.00';
    return '₹ ' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
      {/* Canonical Wording Disclaimer Banner per FR-EXC-019 and SCR-023 */}
      <div
        style={{
          padding: '10px 16px',
          backgroundColor: tokens.semantic.disclaimer.bannerBg,
          borderBottom: `1px solid ${tokens.semantic.disclaimer.bannerBorder}`,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '12px',
          color: tokens.semantic.disclaimer.text,
        }}
      >
        <span style={{ fontSize: '14px' }}>ⓘ</span>
        <span>
          <strong>"{tokens.semantic.disclaimer.canonicalPhrase}"</strong> These items represent patterns flagged for investigation, never a definitive error verdict.
        </span>
      </div>

      <div style={{ overflowX: 'auto', maxHeight: '600px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead style={{ position: 'sticky', top: 0, backgroundColor: '#f8fafc', zIndex: 1, borderBottom: '2px solid #e2e8f0' }}>
            <tr>
              <th style={{ padding: '10px 12px', width: '40px' }}>
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={(input) => {
                    if (input) input.indeterminate = someSelected;
                  }}
                  onChange={(e) => onSelectAll(e.target.checked)}
                />
              </th>
              <th style={{ padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Rule (Pattern)</th>
              <th style={{ padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Subject Key / Entity</th>
              <th style={{ padding: '10px 12px', fontWeight: 600, color: '#475569', textAlign: 'right' }}>Amount at Risk</th>
              <th style={{ padding: '10px 12px', fontWeight: 600, color: '#475569', textAlign: 'center' }}>Severity</th>
              <th style={{ padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Owner</th>
              <th style={{ padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Status</th>
              <th style={{ padding: '10px 12px', fontWeight: 600, color: '#475569', textAlign: 'center' }}>Age &amp; Overdue</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '40px 16px', textAlign: 'center', color: '#64748b' }}>
                  <div style={{ fontSize: '15px', fontWeight: 600, marginBottom: '6px' }}>
                    No open exceptions — nothing requires review.
                  </div>
                  <div style={{ fontSize: '12px' }}>
                    All rules evaluated cleanly or matching the current filter set.
                  </div>
                </td>
              </tr>
            ) : (
              items.map((item) => {
                const isSelected = selectedIds.includes(item.exception_id);
                const sevToken =
                  item.severity.toLowerCase() === 'high'
                    ? tokens.severity.high
                    : item.severity.toLowerCase() === 'low'
                    ? tokens.severity.low
                    : tokens.severity.medium;

                const statusToken = (tokens.status as any)[item.status] || tokens.status.open;

                return (
                  <tr
                    key={item.exception_id}
                    onClick={() => onRowClick(item)}
                    style={{
                      borderBottom: '1px solid #f1f5f9',
                      backgroundColor: isSelected ? '#f0f9ff' : '#ffffff',
                      cursor: 'pointer',
                      transition: 'background-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) e.currentTarget.style.backgroundColor = '#f8fafc';
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) e.currentTarget.style.backgroundColor = '#ffffff';
                    }}
                  >
                    <td
                      style={{ padding: '10px 12px' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRow(item.exception_id, !isSelected);
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => onSelectRow(item.exception_id, e.target.checked)}
                      />
                    </td>

                    {/* Rule name */}
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>
                        {item.rule_id}: {item.rule_name}
                      </div>
                      <div style={{ fontSize: '11px', color: '#64748b', display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span>Hash: {item.identity_hash.substring(0, 8)}...</span>
                        {item.flagged_again && (
                          <span
                            style={{
                              padding: '1px 5px',
                              borderRadius: '3px',
                              backgroundColor: tokens.semantic.flaggedAgain.bg,
                              color: tokens.semantic.flaggedAgain.text,
                              border: `1px solid ${tokens.semantic.flaggedAgain.border}`,
                              fontSize: '10px',
                              fontWeight: 700,
                            }}
                            title="Closed in a prior run but flagged again upon re-evaluation (FR-EXC-005)"
                          >
                            Flagged again ⚑
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Subject key */}
                    <td style={{ padding: '10px 12px', maxWidth: '280px' }}>
                      <div style={{ fontWeight: 500, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.subject_display || item.subject_key}
                      </div>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                        {item.period_code} &bull; {item.evidence_count} evidence row(s) &bull; {item.notes_count} note(s)
                      </div>
                    </td>

                    {/* Amount at risk */}
                    <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 600, color: '#0f172a', fontVariantNumeric: 'tabular-nums' }}>
                      {formatCurrency(item.amount_at_risk)}
                    </td>

                    {/* Severity Badge with Non-colour text symbol per CF-004..006 */}
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          backgroundColor: sevToken.bg,
                          color: sevToken.text,
                          border: `1px solid ${sevToken.border}`,
                          fontWeight: 700,
                          fontSize: '11px',
                        }}
                      >
                        {sevToken.symbol}
                      </span>
                    </td>

                    {/* Owner */}
                    <td style={{ padding: '10px 12px' }}>
                      <span
                        style={{
                          color: item.owner_name === 'Unassigned' ? '#b45309' : '#1e293b',
                          fontWeight: item.owner_name === 'Unassigned' ? 600 : 500,
                          fontStyle: item.owner_name === 'Unassigned' ? 'italic' : 'normal',
                        }}
                      >
                        {item.owner_name}
                      </span>
                    </td>

                    {/* Status */}
                    <td style={{ padding: '10px 12px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          backgroundColor: statusToken.bg,
                          color: statusToken.text,
                          fontSize: '11px',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                        }}
                      >
                        {statusToken.label}
                      </span>
                    </td>

                    {/* Aging and Overdue */}
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: '#334155' }}>
                          {item.days_open}d ({item.aging_bucket})
                        </span>
                        {item.is_overdue && (
                          <span
                            style={{
                              padding: '1px 6px',
                              borderRadius: '3px',
                              backgroundColor: tokens.aging.overdue.bg,
                              color: tokens.aging.overdue.text,
                              border: `1px solid ${tokens.aging.overdue.border}`,
                              fontSize: '10px',
                              fontWeight: 700,
                            }}
                          >
                            Overdue +{item.overdue_days}d ⚠
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { ExceptionDetailResponse, ExceptionStatus } from './types';
import { tokens } from '../../theme/tokens';

interface ExceptionDetailDrawerProps {
  detail: ExceptionDetailResponse | null;
  onClose: () => void;
  onUpdateStatus: (newStatus: ExceptionStatus, note?: string) => void;
  onUpdateOwner: (newOwner: string) => void;
  onAddNote: (note: string) => void;
  isSaving: boolean;
}

export const ExceptionDetailDrawer: React.FC<ExceptionDetailDrawerProps> = ({
  detail,
  onClose,
  onUpdateStatus,
  onUpdateOwner,
  onAddNote,
  isSaving,
}) => {
  if (!detail) return null;

  const { exception, sampleRows, evidenceRefs, notes, events } = detail;
  const [activePane, setActivePane] = useState<'evidence' | 'workflow' | 'history'>('evidence');
  const [statusNote, setStatusNote] = useState('');
  const [newNote, setNewNote] = useState('');
  const [targetStatus, setTargetStatus] = useState<ExceptionStatus>(exception.status);
  const [targetOwner, setTargetOwner] = useState(exception.owner_name);

  const statusTransitions: Record<ExceptionStatus, ExceptionStatus[]> = {
    open: ['in_review', 'not_applicable'],
    in_review: ['explained', 'not_applicable'],
    explained: ['corrected', 'not_applicable'],
    corrected: ['closed'],
    closed: ['reopened'],
    reopened: ['in_review', 'not_applicable'],
    not_applicable: ['reopened'],
  };
  const availableStatuses = new Set<ExceptionStatus>([
    exception.status,
    ...statusTransitions[exception.status],
  ]);
  const standardStatuses: ExceptionStatus[] = [
    'open',
    'in_review',
    'explained',
    'corrected',
    'closed',
  ];
  const statusWorkflow = Array.from(new Set<ExceptionStatus>([
    ...standardStatuses.filter((status) => availableStatuses.has(status)),
    exception.status,
  ]));

  const handleStatusSubmit = (status: ExceptionStatus) => {
    if (['corrected', 'reopened', 'not_applicable'].includes(status) && !statusNote.trim()) {
      alert(`Per FR-EXC-006: "${status.replace('_', ' ')}" requires a non-empty reason or note.`);
      return;
    }
    onUpdateStatus(status, statusNote.trim() || undefined);
    setStatusNote('');
  };

  const handleNoteSubmit = () => {
    if (!newNote.trim()) return;
    onAddNote(newNote.trim());
    setNewNote('');
  };

  const handleOwnerSubmit = () => {
    if (targetOwner === exception.owner_name) return;
    onUpdateOwner(targetOwner);
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: '640px',
        maxWidth: '90vw',
        height: '100vh',
        backgroundColor: '#ffffff',
        boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.15)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Drawer Header */}
      <div
        style={{
          padding: '20px 24px',
          borderBottom: '1px solid #e2e8f0',
          backgroundColor: '#f8fafc',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                backgroundColor: '#e2e8f0',
                color: '#334155',
              }}
            >
              {exception.rule_id}
            </span>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                backgroundColor:
                  exception.severity.toLowerCase() === 'high'
                    ? tokens.severity.high.bg
                    : exception.severity.toLowerCase() === 'low'
                    ? tokens.severity.low.bg
                    : tokens.severity.medium.bg,
                color:
                  exception.severity.toLowerCase() === 'high'
                    ? tokens.severity.high.text
                    : exception.severity.toLowerCase() === 'low'
                    ? tokens.severity.low.text
                    : tokens.severity.medium.text,
              }}
            >
              {exception.severity.toUpperCase()}
            </span>
            {exception.flagged_again && (
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  backgroundColor: tokens.semantic.flaggedAgain.bg,
                  color: tokens.semantic.flaggedAgain.text,
                }}
              >
                Flagged again ⚑
              </span>
            )}
          </div>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>
            {exception.rule_name}
          </h3>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
            Subject: {exception.subject_display || exception.subject_key}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => {
              window.open(`/api/v1/exceptions/${exception.exception_id}/evidence`, '_blank');
            }}
            style={{
              padding: '6px 12px',
              backgroundColor: '#16a34a',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            📥 Download Evidence Bundle (.xlsx)
          </button>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '20px',
              color: '#64748b',
              cursor: 'pointer',
              padding: '4px',
            }}
          >
            ✕
          </button>
        </div>
      </div>

      {/* Navigation Tabs (Evidence, Workflow, History) per SCR-024 */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', backgroundColor: '#ffffff' }}>
        {[
          { id: 'evidence', label: `Evidence Rows (${sampleRows.length || exception.evidence_count})` },
          { id: 'workflow', label: 'Workflow & Notes' },
          { id: 'history', label: `Audit Trail (${events.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActivePane(tab.id as any)}
            style={{
              flex: 1,
              padding: '12px 16px',
              border: 'none',
              borderBottom: activePane === tab.id ? '2px solid #0284c7' : '2px solid transparent',
              backgroundColor: 'transparent',
              fontWeight: activePane === tab.id ? 600 : 500,
              color: activePane === tab.id ? '#0284c7' : '#64748b',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Drawer Body Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        {/* Pane 1: Evidence Rows */}
        {activePane === 'evidence' && (
          <div>
            <div
              style={{
                marginBottom: '16px',
                padding: '12px',
                backgroundColor: '#f8fafc',
                borderRadius: '6px',
                border: '1px solid #e2e8f0',
                fontSize: '12px',
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '8px',
              }}
            >
              <div>
                <strong>Amount at Risk:</strong> ₹{parseFloat(exception.amount_at_risk).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
              <div>
                <strong>Effective Threshold:</strong> {exception.effective_threshold || 'Rule Default'}
              </div>
              <div>
                <strong>Period:</strong> {exception.period_code}
              </div>
              <div>
                <strong>Age:</strong> {exception.days_open} days ({exception.aging_bucket})
              </div>
            </div>

            <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#1e293b', marginBottom: '8px' }}>
              Subject Evidence Rows
            </h4>

            {sampleRows.length > 0 ? (
              <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: '6px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                    <tr>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Voucher / Ref</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Date</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Account</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Vendor</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sampleRows.map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '8px' }}>{row.voucher_no || row.source_row_ref || `Row ${idx + 1}`}</td>
                        <td style={{ padding: '8px' }}>{row.posting_date || row.document_date || '—'}</td>
                        <td style={{ padding: '8px' }}>{row.account_code || '—'}</td>
                        <td style={{ padding: '8px' }}>{row.vendor_code || row.invoice_no || '—'}</td>
                        <td style={{ padding: '8px', textAlign: 'right', fontWeight: 600 }}>
                          ₹{parseFloat(row.amount || row.net_amount || row.debit || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: '6px', color: '#64748b', fontSize: '13px' }}>
                Evidence references recorded: {evidenceRefs.join(', ') || 'No transaction row breakdown available.'}
              </div>
            )}
          </div>
        )}

        {/* Pane 2: Workflow & Notes */}
        {activePane === 'workflow' && (
          <div>
            {/* Status Workflow Stepper */}
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '12px' }}>
                Status Lifecycle: Open → In Review → Explained → Corrected → Closed
              </h4>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
                {statusWorkflow.map((st) => {
                  const isActive = exception.status === st;
                  return (
                    <button
                      key={st}
                      onClick={() => setTargetStatus(st)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        border: isActive ? '2px solid #0284c7' : '1px solid #cbd5e1',
                        backgroundColor: isActive ? '#f0f9ff' : '#ffffff',
                        color: isActive ? '#0284c7' : '#334155',
                        fontWeight: isActive ? 700 : 500,
                        fontSize: '12px',
                        cursor: 'pointer',
                        textTransform: 'capitalize',
                      }}
                    >
                      {st.replace('_', ' ')}
                    </button>
                  );
                })}

                {availableStatuses.has('reopened') && (
                  <button
                    onClick={() => setTargetStatus('reopened')}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: exception.status === 'reopened' ? '2px solid #ea580c' : '1px solid #fed7aa',
                      backgroundColor: exception.status === 'reopened' ? '#fff7ed' : '#ffffff',
                      color: '#c2410c',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    Reopen
                  </button>
                )}
                {availableStatuses.has('not_applicable') && (
                  <button
                    onClick={() => setTargetStatus('not_applicable')}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: exception.status === 'not_applicable' ? '2px solid #9333ea' : '1px solid #e9d5ff',
                      backgroundColor: exception.status === 'not_applicable' ? '#faf5ff' : '#ffffff',
                      color: '#7e22ce',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    Not Applicable
                  </button>
                )}
              </div>

              {targetStatus !== exception.status && (
                <div style={{ padding: '12px', backgroundColor: '#f0f9ff', borderRadius: '6px', border: '1px solid #bae6fd' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#0369a1', marginBottom: '4px' }}>
                    {targetStatus === 'corrected'
                      ? 'Correction note (Required per FR-EXC-006):'
                      : 'Transition explanation / note:'}
                  </label>
                  <textarea
                    rows={2}
                    value={statusNote}
                    onChange={(e) => setStatusNote(e.target.value)}
                    placeholder={targetStatus === 'corrected' ? 'Describe what was corrected in GL/ERP...' : 'Add reason for status change...'}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid #cbd5e1',
                      fontSize: '12px',
                      marginBottom: '8px',
                    }}
                  />
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => handleStatusSubmit(targetStatus)}
                      disabled={isSaving}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#0284c7',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '4px',
                        fontWeight: 600,
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      {isSaving ? 'Saving...' : `Confirm Change to ${targetStatus.replace('_', ' ')}`}
                    </button>
                    <button
                      onClick={() => {
                        setTargetStatus(exception.status);
                        setStatusNote('');
                      }}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#f1f5f9',
                        color: '#64748b',
                        border: '1px solid #cbd5e1',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Owner Assignment */}
            <div style={{ marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
              <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '8px' }}>
                Assigned Owner (FR-EXC-007)
              </h4>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <select
                  value={targetOwner}
                  onChange={(e) => setTargetOwner(e.target.value)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '4px',
                    border: '1px solid #cbd5e1',
                    fontSize: '13px',
                    minWidth: '200px',
                  }}
                >
                  <option value="Unassigned">Unassigned</option>
                  <option value="Rahul">Rahul (Senior Accountant)</option>
                  <option value="Aarti">Aarti (Controller)</option>
                  <option value="Priya">Priya (Staff Accountant)</option>
                  <option value="Sanjay">Sanjay (FP&amp;A Lead)</option>
                </select>
                {targetOwner !== exception.owner_name && (
                  <button
                    onClick={handleOwnerSubmit}
                    disabled={isSaving}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#0284c7',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '4px',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    Save Owner
                  </button>
                )}
              </div>
            </div>

            {/* Append-only Notes Thread (FR-EXC-008) */}
            <div>
              <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '8px' }}>
                Notes Thread ({notes.length})
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                {notes.length === 0 ? (
                  <div style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>
                    No notes recorded yet.
                  </div>
                ) : (
                  notes.map((n) => (
                    <div
                      key={n.noteId}
                      style={{
                        padding: '10px 12px',
                        backgroundColor: '#f8fafc',
                        borderRadius: '6px',
                        border: '1px solid #e2e8f0',
                        fontSize: '12px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <strong style={{ color: '#0f172a' }}>{n.author}</strong>
                        <span style={{ color: '#94a3b8' }}>{n.createdAt}</span>
                      </div>
                      <div style={{ color: '#334155' }}>{n.noteText}</div>
                    </div>
                  ))
                )}
              </div>

              {/* Add Note Form */}
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="Add note to exception history..."
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleNoteSubmit();
                  }}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    borderRadius: '4px',
                    border: '1px solid #cbd5e1',
                    fontSize: '12px',
                  }}
                />
                <button
                  onClick={handleNoteSubmit}
                  disabled={!newNote.trim() || isSaving}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#0284c7',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    fontWeight: 600,
                    fontSize: '12px',
                    cursor: !newNote.trim() ? 'not-allowed' : 'pointer',
                  }}
                >
                  Add Note
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Pane 3: Audit Trail / History */}
        {activePane === 'history' && (
          <div>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '12px' }}>
              Append-Only Audit History
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {events.map((ev) => (
                <div
                  key={ev.eventId}
                  style={{
                    padding: '10px 12px',
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span style={{ fontWeight: 600, color: '#0f172a', textTransform: 'capitalize' }}>
                      {ev.eventType.replace('_', ' ')}
                    </span>
                    <span style={{ color: '#94a3b8', fontSize: '11px' }}>{ev.occurredAt}</span>
                  </div>
                  <div style={{ color: '#475569' }}>
                    Actor: <strong>{ev.actor}</strong> &bull; {ev.noteText || `${ev.fromValue || ''} → ${ev.toValue || ''}`}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

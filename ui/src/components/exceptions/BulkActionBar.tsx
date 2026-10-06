import React, { useState } from 'react';
import { ExceptionStatus } from './types';

interface BulkActionBarProps {
  selectedCount: number;
  onClearSelection: () => void;
  onBulkUpdate: (status?: ExceptionStatus, owner?: string, note?: string) => void;
  isSaving: boolean;
}

export const BulkActionBar: React.FC<BulkActionBarProps> = ({
  selectedCount,
  onClearSelection,
  onBulkUpdate,
  isSaving,
}) => {
  const [targetStatus, setTargetStatus] = useState<string>('');
  const [targetOwner, setTargetOwner] = useState<string>('');
  const [note, setNote] = useState<string>('');

  if (selectedCount === 0) return null;

  const handleApply = () => {
    if (!targetStatus && !targetOwner) {
      alert('Please select a target status or target owner for bulk update.');
      return;
    }
    if (['corrected', 'reopened', 'not_applicable'].includes(targetStatus) && !note.trim()) {
      alert(`A reason or correction note is required for bulk status "${targetStatus.replace('_', ' ')}".`);
      return;
    }
    const statusVal = targetStatus ? (targetStatus as ExceptionStatus) : undefined;
    const ownerVal = targetOwner ? targetOwner : undefined;
    onBulkUpdate(statusVal, ownerVal, note.trim() || undefined);
    setTargetStatus('');
    setTargetOwner('');
    setNote('');
  };

  return (
    <div
      style={{
        position: 'sticky',
        bottom: '20px',
        backgroundColor: '#0f172a',
        color: '#ffffff',
        borderRadius: '8px',
        padding: '12px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
        zIndex: 50,
        marginTop: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontWeight: 700, fontSize: '13px', color: '#38bdf8' }}>
          {selectedCount} item{selectedCount > 1 ? 's' : ''} selected
        </span>
        <button
          onClick={onClearSelection}
          style={{
            background: 'none',
            border: 'none',
            color: '#94a3b8',
            fontSize: '12px',
            textDecoration: 'underline',
            cursor: 'pointer',
          }}
        >
          Deselect all
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <select
          value={targetStatus}
          onChange={(e) => setTargetStatus(e.target.value)}
          style={{
            padding: '6px 10px',
            borderRadius: '4px',
            fontSize: '12px',
            border: '1px solid #334155',
            backgroundColor: '#1e293b',
            color: '#f8fafc',
          }}
        >
          <option value="">Change Status...</option>
          <option value="open">Open</option>
          <option value="in_review">In Review</option>
          <option value="explained">Explained</option>
          <option value="corrected">Corrected</option>
          <option value="closed">Closed</option>
          <option value="reopened">Reopened</option>
          <option value="not_applicable">Not Applicable</option>
        </select>

        <select
          value={targetOwner}
          onChange={(e) => setTargetOwner(e.target.value)}
          style={{
            padding: '6px 10px',
            borderRadius: '4px',
            fontSize: '12px',
            border: '1px solid #334155',
            backgroundColor: '#1e293b',
            color: '#f8fafc',
          }}
        >
          <option value="">Assign Owner...</option>
          <option value="Unassigned">Unassigned</option>
          <option value="Rahul">Rahul (Senior Accountant)</option>
          <option value="Aarti">Aarti (Controller)</option>
          <option value="Priya">Priya (Staff Accountant)</option>
          <option value="Sanjay">Sanjay (FP&amp;A Lead)</option>
        </select>

        <input
          type="text"
          placeholder={['corrected', 'reopened', 'not_applicable'].includes(targetStatus)
            ? 'Required reason or correction note...'
            : 'Optional bulk note...'}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          style={{
            padding: '6px 10px',
            borderRadius: '4px',
            fontSize: '12px',
            border: '1px solid #334155',
            backgroundColor: '#1e293b',
            color: '#f8fafc',
            width: '180px',
          }}
        />

        <button
          onClick={handleApply}
          disabled={isSaving}
          style={{
            padding: '6px 16px',
            backgroundColor: '#38bdf8',
            color: '#0f172a',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 700,
            fontSize: '12px',
            cursor: isSaving ? 'not-allowed' : 'pointer',
          }}
        >
          {isSaving ? 'Updating...' : 'Apply Bulk Action'}
        </button>
      </div>
    </div>
  );
};

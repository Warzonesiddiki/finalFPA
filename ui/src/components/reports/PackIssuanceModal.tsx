import React, { useState } from 'react';

interface PackIssuanceModalProps {
  onClose: () => void;
  onSubmit: (recipients: string[], notes: string) => Promise<void>;
}

export const PackIssuanceModal: React.FC<PackIssuanceModalProps> = ({ onClose, onSubmit }) => {
  const [recipientInput, setRecipientInput] = useState<string>('cfo@acme.com, board@acme.com, controller@acme.com');
  const [notes, setNotes] = useState<string>('Official Month-End Issuance FY26-P09 for Board Review');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const recipients = recipientInput
      .split(',')
      .map((r) => r.trim())
      .filter((r) => r.length > 0);

    if (recipients.length === 0) {
      setError('At least one named recipient or email is required for official issuance.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onSubmit(recipients, notes);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to issue pack');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        backdropFilter: 'blur(2px)',
      }}
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '10px',
          width: '560px',
          maxWidth: '92vw',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e2e8f0',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #e2e8f0',
            backgroundColor: '#f8fafc',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#0f172a' }}>
              📜 Issue Month-End Pack (SCR-030)
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>
              FR-XC-002 &bull; FR-XC-003 Pack Version Increment & Commentary Lock
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '20px',
              cursor: 'pointer',
              color: '#64748b',
            }}
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '20px' }}>
          {error && (
            <div
              style={{
                marginBottom: '16px',
                padding: '10px 14px',
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '6px',
                color: '#dc2626',
                fontSize: '12px',
              }}
            >
              ⚠️ {error}
            </div>
          )}

          <div
            style={{
              padding: '12px 14px',
              backgroundColor: '#fffbeb',
              border: '1px solid #fef3c7',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#92400e',
              marginBottom: '16px',
              lineHeight: 1.4,
            }}
          >
            🔒 <strong>Issuance Invariants (FR-XC-002 / FR-XC-003):</strong>
            <ul style={{ margin: '6px 0 0', paddingLeft: '18px' }}>
              <li>Increments the pack version monotonically (e.g. v1 &rarr; v2).</li>
              <li>Freezes the financial snapshot and locks all active commentary.</li>
              <li>Subsequent edits will require a formal re-issue with audit reason.</li>
            </ul>
          </div>

          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Recipients (comma-separated list) <span style={{ color: '#dc2626' }}>*</span>
            </label>
            <input
              type="text"
              required
              value={recipientInput}
              onChange={(e) => setRecipientInput(e.target.value)}
              placeholder="cfo@acme.com, board@acme.com, auditteam@acme.com"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '13px',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Issuance Notes / Context
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '13px',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '8px 14px',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '13px',
                color: '#475569',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: '8px 18px',
                backgroundColor: '#059669',
                border: 'none',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                color: '#ffffff',
                cursor: submitting ? 'not-allowed' : 'pointer',
                opacity: submitting ? 0.7 : 1,
              }}
            >
              {submitting ? 'Issuing...' : 'Confirm & Issue Pack ▸'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

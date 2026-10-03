import React, { useState } from 'react';

interface PackReissueModalProps {
  issueId: number;
  currentVersion: number;
  onClose: () => void;
  onSubmit: (issueId: number, reason: string) => Promise<void>;
}

export const PackReissueModal: React.FC<PackReissueModalProps> = ({
  issueId,
  currentVersion,
  onClose,
  onSubmit,
}) => {
  const [reason, setReason] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      setError('A mandatory reason is required explaining why this pack is being re-issued.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onSubmit(issueId, reason.trim());
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to re-issue pack');
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
          width: '540px',
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
              🔄 Re-Issue Month-End Pack (SCR-030)
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>
              FR-XC-003 &bull; Supercedes v{currentVersion} &rarr; Creates New Version v{currentVersion + 1}
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
              backgroundColor: '#eff6ff',
              border: '1px solid #bfdbfe',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#1e40af',
              marginBottom: '16px',
              lineHeight: 1.4,
            }}
          >
            ℹ️ <strong>Immutability Guarantee:</strong> Previous pack version <strong>v{currentVersion}</strong> will be marked as <code>superseded</code> but remains permanently frozen in the audit trail. The new issue will increment to <strong>v{currentVersion + 1}</strong>.
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Mandatory Re-issue Audit Reason <span style={{ color: '#dc2626' }}>*</span>
            </label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Revised executive narrative after late audit adjustments in repairs account #5200"
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
                backgroundColor: '#0284c7',
                border: 'none',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                color: '#ffffff',
                cursor: submitting ? 'not-allowed' : 'pointer',
                opacity: submitting ? 0.7 : 1,
              }}
            >
              {submitting ? 'Re-issuing...' : `Create Version v${currentVersion + 1} ▸`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

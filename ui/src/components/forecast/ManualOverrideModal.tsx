import React, { useState } from 'react';
import { ForecastLineDTO } from './types';

interface ManualOverrideModalProps {
  line: ForecastLineDTO | null;
  periodCode: string;
  currentAmount: string;
  onClose: () => void;
  onSubmit: (accountId: number, periodCode: string, amount: string, reason: string) => Promise<void>;
}

export const ManualOverrideModal: React.FC<ManualOverrideModalProps> = ({
  line,
  periodCode,
  currentAmount,
  onClose,
  onSubmit,
}) => {
  const [amount, setAmount] = useState(currentAmount);
  const [reason, setReason] = useState(line?.override_reason || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!line) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      setError('A mandatory reason is required for manual overrides per CALC-064 / FR-FC-006.');
      return;
    }
    if (isNaN(Number(amount)) || Number(amount) < 0) {
      setError('Please provide a valid numeric amount.');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await onSubmit(line.account_id, periodCode, amount, reason.trim());
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to save manual override');
    } finally {
      setSaving(false);
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
          width: '520px',
          maxWidth: '90vw',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '18px' }}>⚙️</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: '#0f172a' }}>
                Manual Forecast Override
              </h3>
              <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>
                FR-FC-006 &bull; CALC-064 Mandatory Reason Audit Trail
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '18px',
              cursor: 'pointer',
              color: '#64748b',
              padding: '4px',
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
                lineHeight: 1.4,
              }}
            >
              ⚠️ {error}
            </div>
          )}

          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Account & Line
            </label>
            <div
              style={{
                padding: '8px 12px',
                backgroundColor: '#f1f5f9',
                borderRadius: '6px',
                fontSize: '13px',
                color: '#1e293b',
                fontWeight: 500,
              }}
            >
              <strong>{line.account_code}</strong> &mdash; {line.account_name} ({line.statement_line})
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Target Period
              </label>
              <div
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: '#0284c7',
                }}
              >
                {periodCode}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                New Amount (₹)
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: '1px solid #cbd5e1',
                  fontSize: '13px',
                  fontFamily: 'monospace',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Mandatory Override Reason <span style={{ color: '#dc2626' }}>*</span>
            </label>
            <textarea
              required
              rows={3}
              placeholder="e.g. Contract signed for Q4 implementation; revised milestone billing per VP approval"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '13px',
                boxSizing: 'border-box',
                resize: 'vertical',
              }}
            />
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
              Reason will be permanently stamped in the FactForecast audit trail and visible in pack reports.
            </div>
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
                fontWeight: 500,
                color: '#475569',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              style={{
                padding: '8px 18px',
                backgroundColor: '#0284c7',
                border: 'none',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                color: '#ffffff',
                cursor: saving ? 'not-allowed' : 'pointer',
                opacity: saving ? 0.7 : 1,
              }}
            >
              {saving ? 'Applying...' : 'Apply Override ⚑'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

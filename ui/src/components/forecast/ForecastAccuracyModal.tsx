import React, { useEffect, useState } from 'react';
import { ForecastAccuracyReportData } from './types';

interface ForecastAccuracyModalProps {
  sessionToken: string;
  onClose: () => void;
}

export const ForecastAccuracyModal: React.FC<ForecastAccuracyModalProps> = ({ sessionToken, onClose }) => {
  const [report, setReport] = useState<ForecastAccuracyReportData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAccuracy();
  }, []);

  const fetchAccuracy = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/forecast/accuracy', {
        headers: { 'X-Session-Token': sessionToken },
      });
      const json = await res.json();
      if (json.status === 'ok') {
        setReport(json.data);
      } else {
        setError(json.detail || 'Failed to load accuracy report');
      }
    } catch (err: any) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (valStr?: string) => {
    if (!valStr) return '₹0.00';
    const num = parseFloat(valStr);
    return isNaN(num) ? '₹0.00' : '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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
          width: '720px',
          maxWidth: '92vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
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
              🎯 Forecast Accuracy & Back-Test Report
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>
              FR-FC-007 / FR-FC-008 &bull; CALC-066..069 Error, Bias, and MAPE-lite Analysis
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

        <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Evaluating forecast accuracy...</div>
          ) : error ? (
            <div style={{ padding: '14px', backgroundColor: '#fef2f2', color: '#dc2626', borderRadius: '6px' }}>
              ⚠️ {error}
            </div>
          ) : report ? (
            <div>
              {/* Summary Metrics Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
                <div style={{ padding: '14px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Signed Bias</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', marginTop: '4px', fontFamily: 'monospace' }}>
                    {formatMoney(report.signedBias)}
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>Avg signed error</div>
                </div>

                <div style={{ padding: '14px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Absolute Error</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', marginTop: '4px', fontFamily: 'monospace' }}>
                    {formatMoney(report.absoluteError)}
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>Total abs error</div>
                </div>

                <div style={{ padding: '14px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>MAPE-lite</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0284c7', marginTop: '4px', fontFamily: 'monospace' }}>
                    {report.mapeLite ? `${report.mapeLite}%` : 'N/A'}
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>Mean abs pct error</div>
                </div>

                <div style={{ padding: '14px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>Periods Evaluated</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', marginTop: '4px', fontFamily: 'monospace' }}>
                    {report.periodCount}
                  </div>
                  <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>P01..P09 closed</div>
                </div>
              </div>

              {/* Guidance Callout */}
              <div
                style={{
                  padding: '14px 16px',
                  backgroundColor: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  borderRadius: '8px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, color: '#166534', fontSize: '13px' }}>
                  <span>💡</span> Forecast Method Guidance (CALC-069):
                </div>
                <div style={{ fontSize: '13px', color: '#14532d', marginTop: '6px', lineHeight: 1.5 }}>
                  {report.guidanceNote}
                </div>
              </div>

              {/* Mathematical Invariants */}
              <div
                style={{
                  padding: '12px 14px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: '#64748b',
                  lineHeight: 1.5,
                }}
              >
                <strong>Evaluation Invariant:</strong> Signed error = Forecast &minus; Actual. Zero-actual periods excluded from percentage error division: <strong>{report.zeroPeriodsExcluded}</strong>.
              </div>
            </div>
          ) : null}
        </div>

        <div
          style={{
            padding: '12px 20px',
            borderTop: '1px solid #e2e8f0',
            backgroundColor: '#f8fafc',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <button
            onClick={onClose}
            style={{
              padding: '8px 18px',
              backgroundColor: '#0284c7',
              border: 'none',
              borderRadius: '6px',
              color: '#ffffff',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

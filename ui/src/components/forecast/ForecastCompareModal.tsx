import React, { useEffect, useState } from 'react';
import { ScenarioCompareRow } from './types';

interface ForecastCompareModalProps {
  sessionToken: string;
  onClose: () => void;
}

export const ForecastCompareModal: React.FC<ForecastCompareModalProps> = ({ sessionToken, onClose }) => {
  const [data, setData] = useState<ScenarioCompareRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCompare();
  }, []);

  const fetchCompare = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/forecast/compare', {
        headers: { 'X-Session-Token': sessionToken },
      });
      const json = await res.json();
      if (json.status === 'ok') {
        setData(json.data.items || []);
      } else {
        setError(json.detail || 'Failed to load scenario comparison');
      }
    } catch (err: any) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (valStr: string) => {
    const num = parseFloat(valStr || '0');
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
          width: '900px',
          maxWidth: '94vw',
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
              📊 Scenario Comparison & Variance Analysis
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#64748b' }}>
              SCR-028 &bull; Base vs Best (+5% rev, -3% opex) vs Worst (-5% rev, +3% opex) per CALC-065
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

        <div style={{ padding: '16px 20px', overflowY: 'auto', flex: 1 }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Loading scenario comparison...</div>
          ) : error ? (
            <div style={{ padding: '14px', backgroundColor: '#fef2f2', color: '#dc2626', borderRadius: '6px' }}>
              ⚠️ {error}
            </div>
          ) : (
            <div>
              <div
                style={{
                  marginBottom: '16px',
                  padding: '12px 16px',
                  backgroundColor: '#f0f9ff',
                  border: '1px solid #bae6fd',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: '#0369a1',
                }}
              >
                💡 <strong>Deterministic Rules Applied (CALC-065):</strong> Best case reflects +5% top-line upside with 3% cost efficiencies. Worst case reflects -5% downside demand with 3% inflationary opex pressures.
              </div>

              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: '13px',
                }}
              >
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                    <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Account</th>
                    <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Line</th>
                    <th style={{ textAlign: 'right', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Base Case</th>
                    <th style={{ textAlign: 'right', padding: '10px 12px', fontWeight: 600, color: '#166534' }}>Best Case (+5% / -3%)</th>
                    <th style={{ textAlign: 'right', padding: '10px 12px', fontWeight: 600, color: '#991b1b' }}>Worst Case (-5% / +3%)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((row) => (
                    <tr key={row.accountId} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '10px 12px', fontWeight: 500, color: '#1e293b' }}>
                        <span style={{ fontFamily: 'monospace', color: '#0284c7', marginRight: '6px' }}>{row.accountCode}</span>
                        {row.accountName}
                      </td>
                      <td style={{ padding: '10px 12px', color: '#64748b' }}>{row.statementLine}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>
                        {formatMoney(row.base)}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600, color: '#166534', backgroundColor: '#f0fdf4' }}>
                        {formatMoney(row.best)}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600, color: '#991b1b', backgroundColor: '#fef2f2' }}>
                        {formatMoney(row.worst)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
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

import React, { useEffect, useState } from 'react';
import { ForecastWorkspaceData } from './types';
import { ForecastWorkspace } from './ForecastWorkspace';
import { ForecastAccuracyTrendChart } from './ForecastAccuracyTrendChart';
import { StaleBanner } from '../common';

interface ForecastScreenProps {
  sessionToken: string;
}

export const ForecastScreen: React.FC<ForecastScreenProps> = ({ sessionToken }) => {
  const [data, setData] = useState<ForecastWorkspaceData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const fetchWorkspace = async (scenario: string = 'base', method: string = 'run_rate', runRateN: number = 3) => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        scenario,
        default_method: method,
        run_rate_n: String(runRateN),
      });
      const res = await fetch(`/api/v1/forecast/workspace?${params.toString()}`, {
        headers: { 'X-Session-Token': sessionToken },
      });
      const json = await res.json();
      if (json.status === 'ok') {
        setData(json.data);
      } else {
        setError(json.detail || 'Failed to retrieve forecast workspace');
      }
    } catch (err: any) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspace();
  }, [sessionToken]);

  const handleOverrideSubmit = async (
    accountId: number,
    periodCode: string,
    amount: string,
    reason: string
  ) => {
    const res = await fetch('/api/v1/forecast/cells', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        account_id: accountId,
        period_code: periodCode,
        amount,
        reason,
        scenario: data?.scenario || 'base',
      }),
    });
    const json = await res.json();
    if (json.status === 'ok') {
      setSuccessBanner(`Override applied successfully for account #${accountId} (${periodCode}).`);
      setTimeout(() => setSuccessBanner(null), 4000);
      await fetchWorkspace(data?.scenario || 'base');
    } else {
      throw new Error(json.detail || 'Failed to apply override');
    }
  };

  const handleLockVersion = async (versionId: string) => {
    const res = await fetch(`/api/v1/forecast/versions/${encodeURIComponent(versionId)}/lock`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({ confirm: true }),
    });
    const json = await res.json();
    if (json.status === 'ok') {
      setSuccessBanner(`Version "${versionId}" has been locked successfully. Projections frozen for pack issuance.`);
      setTimeout(() => setSuccessBanner(null), 5000);
      await fetchWorkspace(data?.scenario || 'base');
    } else {
      throw new Error(json.detail || 'Failed to lock version');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <StaleBanner sessionToken={sessionToken} onRerunComplete={() => fetchWorkspace()} />
      {/* Toast notifications */}
      {successBanner && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: '6px',
            color: '#166534',
            fontSize: '13px',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span>✓</span> {successBanner}
        </div>
      )}

      {error && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '6px',
            color: '#dc2626',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          ⚠️ {error}
        </div>
      )}

      <ForecastWorkspace
        sessionToken={sessionToken}
        data={data}
        loading={loading}
        onRefresh={fetchWorkspace}
        onOverrideSubmit={handleOverrideSubmit}
        onLockVersion={handleLockVersion}
      />

      <ForecastAccuracyTrendChart
        items={[
          { period: 'FY26-P06', errorPct: 2.1 },
          { period: 'FY26-P07', errorPct: 4.8 },
          { period: 'FY26-P08', errorPct: 1.5 },
          { period: 'FY26-P09', errorPct: 3.2 },
        ]}
      />
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { PackRefDTO, IssuanceRefDTO, CommentaryRowDTO } from './types';
import { PackGeneratorCard } from './PackGeneratorCard';
import { CommentaryEditorCard } from './CommentaryEditorCard';
import { IssuanceRegisterCard } from './IssuanceRegisterCard';

interface ReportsScreenProps {
  sessionToken: string;
}

export const ReportsScreen: React.FC<ReportsScreenProps> = ({ sessionToken }) => {
  const [packs, setPacks] = useState<PackRefDTO[]>([]);
  const [issuanceList, setIssuanceList] = useState<IssuanceRefDTO[]>([]);
  const [commentaries, setCommentaries] = useState<CommentaryRowDTO[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const headers = { 'X-Session-Token': sessionToken };

      const [packsRes, issuanceRes, commRes] = await Promise.all([
        fetch('/api/v1/packs', { headers }),
        fetch('/api/v1/issuance', { headers }),
        fetch('/api/v1/commentary?period_id=9', { headers }),
      ]);

      const [packsJson, issuanceJson, commJson] = await Promise.all([
        packsRes.json(),
        issuanceRes.json(),
        commRes.json(),
      ]);

      if (packsJson.status === 'ok') setPacks(packsJson.data.items || []);
      if (issuanceJson.status === 'ok') setIssuanceList(issuanceJson.data.items || []);
      if (commJson.status === 'ok') setCommentaries(commJson.data.items || []);
    } catch (err: any) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [sessionToken]);

  const handleGenerate = async (format: 'excel' | 'ppt' | 'both', scenario: string) => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/packs/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
        body: JSON.stringify({
          period: 'FY26-P09',
          scenario,
          format,
        }),
      });
      const json = await res.json();
      if (json.status === 'ok') {
        setSuccessBanner(`Pack generated successfully! Built ${json.data.items.length} file artifact(s).`);
        setTimeout(() => setSuccessBanner(null), 5000);
        await fetchData();
      } else {
        throw new Error(json.detail || 'Pack generation failed');
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to generate pack');
    } finally {
      setLoading(false);
    }
  };

  const handleIssue = async (recipients: string[], notes: string) => {
    const res = await fetch('/api/v1/issuance', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        period_id: 9,
        period_code: 'FY26-P09',
        recipients,
        pack_type: 'both',
        notes,
      }),
    });
    const json = await res.json();
    if (json.status === 'ok') {
      setSuccessBanner(`Pack officially issued as v${json.data.pack_version}. Snapshots and commentary locked.`);
      setTimeout(() => setSuccessBanner(null), 6000);
      await fetchData();
    } else {
      throw new Error(json.detail || 'Pack issuance failed');
    }
  };

  const handleReissue = async (issueId: number, reason: string) => {
    const res = await fetch(`/api/v1/issuance/${issueId}/reissue`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        issue_id: issueId,
        reason,
      }),
    });
    const json = await res.json();
    if (json.status === 'ok') {
      setSuccessBanner(`Pack re-issued as v${json.data.pack_version}. Previous version superseded.`);
      setTimeout(() => setSuccessBanner(null), 6000);
      await fetchData();
    } else {
      throw new Error(json.detail || 'Pack re-issuance failed');
    }
  };

  const handleSaveCommentary = async (scopeType: 'line' | 'executive', subjectKey: string, text: string) => {
    const res = await fetch('/api/v1/commentary', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Token': sessionToken,
      },
      body: JSON.stringify({
        period_id: 9,
        scope_type: scopeType,
        subject_key: subjectKey,
        text,
        author: 'Aarti',
      }),
    });
    const json = await res.json();
    if (json.status === 'ok') {
      setSuccessBanner(`Commentary updated for ${subjectKey} (v${json.data.current_version_no}).`);
      setTimeout(() => setSuccessBanner(null), 4000);
      await fetchData();
    } else {
      throw new Error(json.detail || 'Failed to save commentary');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Toast banners */}
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

      {/* 1. Pack Generator Card (SCR-029) */}
      <PackGeneratorCard
        onGenerate={handleGenerate}
        loading={loading}
      />

      {/* 2. Commentary & Narrative Editor (SCR-031) */}
      <CommentaryEditorCard
        commentaries={commentaries}
        loading={loading}
        onSave={handleSaveCommentary}
      />

      {/* 3. Issuance Register & File List (SCR-030) */}
      <IssuanceRegisterCard
        packs={packs}
        issuanceList={issuanceList}
        loading={loading}
        onIssue={handleIssue}
        onReissue={handleReissue}
      />
    </div>
  );
};

import React, { useState } from 'react';
import { PackRefDTO, IssuanceRefDTO } from './types';
import { PackIssuanceModal } from './PackIssuanceModal';
import { PackReissueModal } from './PackReissueModal';

interface IssuanceRegisterCardProps {
  packs: PackRefDTO[];
  issuanceList: IssuanceRefDTO[];
  loading: boolean;
  onIssue: (recipients: string[], notes: string) => Promise<void>;
  onReissue: (issueId: number, reason: string) => Promise<void>;
}

export const IssuanceRegisterCard: React.FC<IssuanceRegisterCardProps> = ({
  packs,
  issuanceList,
  loading,
  onIssue,
  onReissue,
}) => {
  const [showIssueModal, setShowIssueModal] = useState<boolean>(false);
  const [reissueTarget, setReissueTarget] = useState<IssuanceRefDTO | null>(null);

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 KB';
    return (bytes / 1024).toFixed(1) + ' KB';
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        border: '1px solid #e2e8f0',
        padding: '20px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#0f172a' }}>
            📋 Pack Issuance Register & Audit History (SCR-030)
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#64748b' }}>
            FR-XC-003 &bull; Versioned pack issuance, recipient lists, immutable snapshot locks
          </p>
        </div>

        <button
          onClick={() => setShowIssueModal(true)}
          style={{
            padding: '8px 16px',
            backgroundColor: '#059669',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span>📜</span> Issue Pack ▸
        </button>
      </div>

      {/* Issuance History Table */}
      <div style={{ marginBottom: '24px', overflowX: 'auto' }}>
        <h4 style={{ margin: '0 0 10px', fontSize: '13px', fontWeight: 600, color: '#475569' }}>
          Official Pack Issuance Ledger
        </h4>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
              <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Version</th>
              <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Period</th>
              <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Status</th>
              <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Issued To</th>
              <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Date / Issuer</th>
              <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Notes</th>
              <th style={{ textAlign: 'center', padding: '10px 12px', fontWeight: 600, color: '#475569' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading && issuanceList.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                  Loading issuance register...
                </td>
              </tr>
            ) : issuanceList.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                  No packs issued yet for this period. Click "Issue Pack" above to create v1.
                </td>
              </tr>
            ) : (
              issuanceList.map((iss) => (
                <tr key={iss.issue_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 700, color: '#0f172a' }}>
                    v{iss.pack_version}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#0369a1', fontWeight: 600 }}>
                    {iss.period_code}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 600,
                        backgroundColor: iss.status === 'issued' ? '#dcfce7' : '#f1f5f9',
                        color: iss.status === 'issued' ? '#166534' : '#64748b',
                      }}
                    >
                      {iss.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ fontSize: '12px', color: '#1e293b' }}>
                      {iss.recipients.join(', ')}
                    </div>
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: '12px', color: '#64748b' }}>
                    {new Date(iss.issued_at).toLocaleDateString()} by {iss.issued_by}
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: '12px', color: '#475569' }}>
                    {iss.notes || '—'}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    {iss.status === 'issued' && (
                      <button
                        onClick={() => setReissueTarget(iss)}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#ffffff',
                          border: '1px solid #cbd5e1',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 600,
                          color: '#0284c7',
                          cursor: 'pointer',
                        }}
                      >
                        🔄 Re-Issue
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Generated Artifact Files List */}
      <div>
        <h4 style={{ margin: '0 0 10px', fontSize: '13px', fontWeight: 600, color: '#475569' }}>
          Generated File Artifacts
        </h4>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={{ textAlign: 'left', padding: '8px 10px', color: '#64748b' }}>Format</th>
              <th style={{ textAlign: 'left', padding: '8px 10px', color: '#64748b' }}>File Name</th>
              <th style={{ textAlign: 'left', padding: '8px 10px', color: '#64748b' }}>Version</th>
              <th style={{ textAlign: 'left', padding: '8px 10px', color: '#64748b' }}>Scenario</th>
              <th style={{ textAlign: 'right', padding: '8px 10px', color: '#64748b' }}>File Size</th>
              <th style={{ textAlign: 'left', padding: '8px 10px', color: '#64748b' }}>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {packs.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '20px', color: '#94a3b8' }}>
                  No pack files generated yet.
                </td>
              </tr>
            ) : (
              packs.map((p) => (
                <tr key={p.pack_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '8px 10px', fontWeight: 600 }}>
                    {p.pack_token === 'excel' ? '📊 Excel' : '📑 PowerPoint'}
                  </td>
                  <td style={{ padding: '8px 10px', fontFamily: 'monospace', color: '#0369a1' }}>
                    {p.file_name}
                  </td>
                  <td style={{ padding: '8px 10px' }}>v{p.pack_version}</td>
                  <td style={{ padding: '8px 10px', textTransform: 'capitalize' }}>{p.scenario_id}</td>
                  <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'monospace' }}>
                    {formatFileSize(p.file_size_bytes)}
                  </td>
                  <td style={{ padding: '8px 10px', color: '#64748b' }}>
                    {new Date(p.generated_at).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {showIssueModal && (
        <PackIssuanceModal
          onClose={() => setShowIssueModal(false)}
          onSubmit={onIssue}
        />
      )}

      {reissueTarget && (
        <PackReissueModal
          issueId={reissueTarget.issue_id}
          currentVersion={reissueTarget.pack_version}
          onClose={() => setReissueTarget(null)}
          onSubmit={onReissue}
        />
      )}
    </div>
  );
};

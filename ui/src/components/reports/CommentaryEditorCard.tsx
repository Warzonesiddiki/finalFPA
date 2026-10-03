import React, { useState } from 'react';
import { CommentaryRowDTO } from './types';

interface CommentaryEditorCardProps {
  commentaries: CommentaryRowDTO[];
  loading: boolean;
  onSave: (scopeType: 'line' | 'executive', subjectKey: string, text: string) => Promise<void>;
}

export const CommentaryEditorCard: React.FC<CommentaryEditorCardProps> = ({
  commentaries,
  loading,
  onSave,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'executive' | 'line'>('executive');
  const [selectedKey, setSelectedKey] = useState<string>('EXECUTIVE');
  const [editingText, setEditingText] = useState<string>('');
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active commentary
  const currentCommentary = commentaries.find(
    (c) => c.scope_type === activeSubTab && c.subject_key === selectedKey
  );

  // Sync editor when selection changes
  React.useEffect(() => {
    if (currentCommentary) {
      setEditingText(currentCommentary.text);
    } else {
      setEditingText('');
    }
  }, [currentCommentary, activeSubTab, selectedKey]);

  const handleSubTabChange = (tab: 'executive' | 'line') => {
    setActiveSubTab(tab);
    if (tab === 'executive') {
      setSelectedKey('EXECUTIVE');
    } else {
      const firstLine = commentaries.find((c) => c.scope_type === 'line');
      setSelectedKey(firstLine ? firstLine.subject_key : '4000');
    }
  };

  const handleSave = async () => {
    if (!editingText.trim()) {
      setError('Commentary text cannot be blank.');
      return;
    }
    try {
      setSaving(true);
      setError(null);
      await onSave(activeSubTab, selectedKey, editingText.trim());
    } catch (err: any) {
      setError(err?.message || 'Failed to save commentary');
    } finally {
      setSaving(false);
    }
  };

  const isLocked = currentCommentary?.is_locked || false;

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
            📝 Commentary & Narrative Editor (SCR-031)
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#64748b' }}>
            FR-XC-001 (Versioned Commentary) &bull; FR-XC-002 (Locked upon Issuance)
          </p>
        </div>

        <div style={{ display: 'flex', gap: '4px', backgroundColor: '#f1f5f9', padding: '3px', borderRadius: '6px' }}>
          <button
            onClick={() => handleSubTabChange('executive')}
            style={{
              padding: '6px 14px',
              border: 'none',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: activeSubTab === 'executive' ? '#ffffff' : 'transparent',
              color: activeSubTab === 'executive' ? '#0f172a' : '#64748b',
              cursor: 'pointer',
              boxShadow: activeSubTab === 'executive' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
            }}
          >
            Executive Narrative
          </button>
          <button
            onClick={() => handleSubTabChange('line')}
            style={{
              padding: '6px 14px',
              border: 'none',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: activeSubTab === 'line' ? '#ffffff' : 'transparent',
              color: activeSubTab === 'line' ? '#0f172a' : '#64748b',
              cursor: 'pointer',
              boxShadow: activeSubTab === 'line' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
            }}
          >
            Per-Line Variance Commentary
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '10px 14px', backgroundColor: '#fef2f2', color: '#dc2626', borderRadius: '6px', marginBottom: '14px', fontSize: '12px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Line selection tabs if per-line */}
      {activeSubTab === 'line' && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', overflowX: 'auto', paddingBottom: '4px' }}>
          {commentaries
            .filter((c) => c.scope_type === 'line')
            .map((c) => (
              <button
                key={c.subject_key}
                onClick={() => setSelectedKey(c.subject_key)}
                style={{
                  padding: '5px 12px',
                  borderRadius: '6px',
                  border: '1px solid',
                  borderColor: selectedKey === c.subject_key ? '#0284c7' : '#cbd5e1',
                  backgroundColor: selectedKey === c.subject_key ? '#f0f9ff' : '#ffffff',
                  color: selectedKey === c.subject_key ? '#0369a1' : '#475569',
                  fontSize: '12px',
                  fontWeight: selectedKey === c.subject_key ? 600 : 500,
                  cursor: 'pointer',
                }}
              >
                Account #{c.subject_key}
              </button>
            ))}
        </div>
      )}

      {/* Editor & Metadata */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            Version: <strong style={{ color: '#0f172a' }}>v{currentCommentary?.current_version_no || 1}</strong> &bull; Author:{' '}
            <strong style={{ color: '#0f172a' }}>{currentCommentary?.author || 'Aarti'}</strong> ({currentCommentary?.source || 'user'})
          </div>

          <div>
            {isLocked ? (
              <span
                style={{
                  padding: '3px 8px',
                  backgroundColor: '#fef3c7',
                  color: '#92400e',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: 600,
                }}
              >
                🔒 Locked by Issuance
              </span>
            ) : (
              <span
                style={{
                  padding: '3px 8px',
                  backgroundColor: '#dcfce7',
                  color: '#166534',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: 600,
                }}
              >
                ✏️ Draft / Editable
              </span>
            )}
          </div>
        </div>

        <textarea
          rows={5}
          value={editingText}
          onChange={(e) => setEditingText(e.target.value)}
          placeholder="Enter formal accounting narrative for executive deck and management pack..."
          style={{
            width: '100%',
            padding: '10px 14px',
            borderRadius: '6px',
            border: '1px solid #cbd5e1',
            fontSize: '13px',
            lineHeight: 1.5,
            boxSizing: 'border-box',
            fontFamily: 'inherit',
          }}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
          <div style={{ fontSize: '11px', color: '#64748b' }}>
            {isLocked
              ? 'Saving will create a new draft version (v' + ((currentCommentary?.current_version_no || 1) + 1) + ') per FR-XC-002.'
              : 'Saving updates this commentary and stamps it in the audit trail.'}
          </div>

          <button
            onClick={handleSave}
            disabled={saving || loading}
            style={{
              padding: '6px 16px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.7 : 1,
            }}
          >
            {saving ? 'Saving...' : isLocked ? 'Create New Version & Save ▸' : 'Save Commentary'}
          </button>
        </div>
      </div>
    </div>
  );
};

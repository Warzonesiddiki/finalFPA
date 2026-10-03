import React, { useState } from 'react';

interface PackGeneratorCardProps {
  onGenerate: (format: 'excel' | 'ppt' | 'both', scenario: string) => Promise<void>;
  loading: boolean;
}

export const PackGeneratorCard: React.FC<PackGeneratorCardProps> = ({ onGenerate, loading }) => {
  const [format, setFormat] = useState<'excel' | 'ppt' | 'both'>('both');
  const [scenario, setScenario] = useState<string>('base');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate(format, scenario);
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#0f172a' }}>
            📦 Generate Output Packs (SCR-029)
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#64748b' }}>
            FR-XL-001..009 (Excel 7-sheet workbook) &bull; FR-PPT-001..009 (6-slide executive deck)
          </p>
        </div>
        <span
          style={{
            padding: '3px 8px',
            backgroundColor: '#f0fdf4',
            color: '#166534',
            borderRadius: '12px',
            fontSize: '11px',
            fontWeight: 600,
          }}
        >
          Phase 5 Validated
        </span>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'flex-end' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
            Output Artifact:
          </label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as any)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '13px',
              backgroundColor: '#ffffff',
              minWidth: '220px',
            }}
          >
            <option value="both">Both (Excel Workbook + PPT Deck)</option>
            <option value="excel">Excel Pack (.xlsx — 7 Sheets)</option>
            <option value="ppt">PowerPoint Deck (.pptx — 6 Slides)</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
            Forecast Scenario:
          </label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '13px',
              backgroundColor: '#ffffff',
              minWidth: '180px',
            }}
          >
            <option value="base">Base Case (Default)</option>
            <option value="best">Best Case (+5% Rev / -3% Opex)</option>
            <option value="worst">Worst Case (-5% Rev / +3% Opex)</option>
          </select>
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '8px 20px',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              opacity: loading ? 0.7 : 1,
            }}
          >
            <span>{loading ? 'Building Pack...' : 'Generate Pack ▸'}</span>
          </button>
        </div>
      </form>

      <div
        style={{
          marginTop: '16px',
          padding: '10px 14px',
          backgroundColor: '#f8fafc',
          borderRadius: '6px',
          border: '1px solid #e2e8f0',
          fontSize: '11px',
          color: '#64748b',
          lineHeight: 1.4,
        }}
      >
        <strong>Canonical Stamping Policy (FR-XL-006 / FR-PPT-009):</strong> Generated files are stamped with Period (<code>FY26-P09</code>), Project, Source Import Batch IDs, User, and full statutory disclaimer. Native, editable format with 0% screenshot rasterization.
      </div>
    </div>
  );
};

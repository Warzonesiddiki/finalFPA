/**
 * Contextual Help Panel Component (FR-ONB-004 / FR-ONB-007)
 *
 * Functional Requirements quoted from docs/02_FUNCTIONAL_SPEC.md & docs/22_END_USER_GUIDE.md:
 * - FR-ONB-004 (Contextual Help Panel): Provides screen-by-screen help text sourced directly from the single-source contract in docs/22, keyed to current active screen.
 * - FR-ONB-007 (Help & FAQ Access): Instantly accessible via the ? menu or shortcut without losing analyst context.
 */



interface HelpPanelProps {
  activeTab: string
  onClose: () => void
}

const HELP_TOPICS: Record<string, { title: string; summary: string; steps: string[]; checkpoint: string }> = {
  home: {
    title: 'Home & Period Overview',
    summary: 'The central dashboard showing current active period status, quick links, and system health.',
    steps: [
      'Check current period indicator (e.g., FY26-P09).',
      'Use quick actions to start a new period or jump to import/analysis.',
      'Review system storage health and backup status.'
    ],
    checkpoint: 'Period status shows active and ready for review or import.'
  },
  import: {
    title: 'Import & Wizard (SCR-001..010)',
    summary: 'Step-by-step guidance to ingest trial balance, GL actuals, bank ledgers, and budgets.',
    steps: [
      'Select source file or drag and drop CSV files.',
      'Map columns and review auto-detected mappings.',
      'Run validation checks and click Commit.'
    ],
    checkpoint: 'Batch status changes to Committed with validation passed.'
  },
  check: {
    title: 'Check & Quality (SCR-011..014)',
    summary: 'Audit data integrity, balance equations, and reconciliation scores.',
    steps: [
      'Review trial balance equality checks.',
      'Inspect any quarantined batches or warnings.',
      'Verify row counts against sample data specifications.'
    ],
    checkpoint: 'All balance checks show Green (PASS).'
  },
  analyze: {
    title: 'Analyse & Variance (SCR-015..019)',
    summary: 'Explore Budget vs Actual matrices, waterfalls, and transaction drill-downs.',
    steps: [
      'Select Department and Cost Center filters.',
      'Click any variance figure to open the transaction evidence drawer.',
      'Compare actual expenditures against budget.'
    ],
    checkpoint: 'Variance grid loaded and drill-down drawer responsive.'
  },
  exceptions: {
    title: 'Exceptions & Review (SCR-020..027)',
    summary: 'Manage automated exception rules EXC-001 to EXC-024 with status workflows.',
    steps: [
      'Filter findings by severity (Critical, Warning, Info).',
      'Assign finding owner and transition status (Open -> In Review -> Explained -> Closed).',
      'Attach explanatory notes and review evidence.'
    ],
    checkpoint: 'Findings correctly categorized and assigned.'
  },
  forecast: {
    title: 'Forecast & Scenarios (SCR-028..032)',
    summary: 'Run monthly forecasts, method comparisons, and Base/Best/Worst scenarios.',
    steps: [
      'Select forecasting method (Run-rate, Trailing Average, Remaining Budget).',
      'Compare Base, Best, and Worst scenario projections.',
      'Enter manual overrides with required justification reasons.'
    ],
    checkpoint: 'Forecast curves updated and scenario comparison visible.'
  },
  reports: {
    title: 'Reports & Issuance (SCR-033..038)',
    summary: 'Generate Excel packs (doc 11) and PowerPoint decks (doc 12) with formal issuance control.',
    steps: [
      'Preview Excel pack sheets and PowerPoint executive slides.',
      'Verify commentary and narrative locks.',
      'Click Issue Pack to increment version and record recipient list.'
    ],
    checkpoint: 'Pack issued successfully with immutable version stamp.'
  },
  settings: {
    title: 'Settings & Master Data',
    summary: 'Configure mapping rules, approval thresholds, brand colors, and storage parameters.',
    steps: [
      'Adjust rule thresholds and enable/disable specific checks.',
      'Configure company branding and display currency formatting.',
      'Manage AI API key settings (write-only interface).'
    ],
    checkpoint: 'Settings saved successfully.'
  },
  backup: {
    title: 'Backup & Restore (SCR-039)',
    summary: 'Manage project backups, compressed archives, and storage health.',
    steps: [
      'Click Download Project Backup Zip to export full state.',
      'Use Select Backup Zip to restore from a previous archive.',
      'Review storage usage breakdown across DuckDB and raw CSV files.'
    ],
    checkpoint: 'Backup archive generated or storage metrics displayed.'
  },
  about: {
    title: 'About & Diagnostics (SCR-040)',
    summary: 'View version metadata, build provenance, CLI doctor checks, and redacted diagnostics export.',
    steps: [
      'Review system version and Windows 11 desktop native metadata.',
      'Click Export Redacted Diagnostics Zip for support bundles (doc 13).',
      'Verify CLI doctor health checks (DOC-01..05).'
    ],
    checkpoint: 'All doctor checks showing PASS status.'
  },
}

export function HelpPanel({ activeTab, onClose }: HelpPanelProps) {
  const topic = HELP_TOPICS[activeTab] || HELP_TOPICS['home']

  return (
    <div style={{ position: 'fixed', top: 0, right: 0, width: '400px', height: '100vh', backgroundColor: '#fff', boxShadow: '-5px 0 25px rgba(0,0,0,0.15)', zIndex: 10000, display: 'flex', flexDirection: 'column', borderLeft: '1px solid #e2e8f0' }}>
      <div style={{ padding: '20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#f8fafc' }}>
        <div>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', color: '#0284c7', fontWeight: 700 }}>Contextual Help (Doc 22)</span>
          <h3 style={{ margin: '4px 0 0', fontSize: '16px', color: '#1e293b' }}>{topic.title}</h3>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#64748b' }}
        >
          ✕
        </button>
      </div>

      <div style={{ padding: '24px', overflowY: 'auto', flex: 1, fontSize: '13px', color: '#334155' }}>
        <p style={{ margin: '0 0 16px', fontWeight: 500, color: '#475569' }}>{topic.summary}</p>

        <h4 style={{ margin: '16px 0 8px', fontSize: '14px', color: '#0f172a' }}>Standard Steps:</h4>
        <ol style={{ margin: '0 0 20px', paddingLeft: '20px', lineHeight: '1.6' }}>
          {topic.steps.map((s, idx) => (
            <li key={idx} style={{ marginBottom: '6px' }}>{s}</li>
          ))}
        </ol>

        <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '12px 16px', marginBottom: '20px' }}>
          <strong style={{ color: '#166534', display: 'block', marginBottom: '4px' }}>✓ Checkpoint:</strong>
          <span style={{ color: '#14532d' }}>{topic.checkpoint}</span>
        </div>

        <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '16px', color: '#64748b', fontSize: '12px' }}>
          Need further assistance? Contact your system administrator or send a diagnostics zip from the <strong>About &amp; Diagnostics</strong> screen.
        </div>
      </div>
    </div>
  )
}

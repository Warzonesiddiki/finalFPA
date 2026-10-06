import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ImportWizard, ImportHistoryScreen } from './components/import'
import { CheckScreen } from './components/check'
import { AnalyzeScreen } from './components/analyze'
import { ExceptionsScreen } from './components/exceptions'
import { ForecastScreen } from './components/forecast'
import { ReportsScreen } from './components/reports'
import { SettingsScreen } from './components/settings'
import { AiCommentaryScreen } from './components/ai'
import { SearchScreen } from './components/search'
import { BackupRestoreScreen } from './components/backup'
import { AboutDiagnosticsScreen } from './components/about'
import { GuidedTour, HelpPanel } from './components/onboarding'

interface HealthInfo {
  status: string
  app: string
  version: string
  engine_ready: boolean
}

interface BatchItem {
  batch_id: number
  file_name: string
  source_type: string
  total_source_rows: number
  loaded_count: number
  quarantined_count: number
  rejected_count: number
  status: string
  is_balanced: number
  total_debit: string
  total_credit: string
  net_imbalance: string
  data_quality_score: number
  created_at: string
}

export function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'import' | 'importhistory' | 'check' | 'analyze' | 'exceptions' | 'forecast' | 'reports' | 'ai' | 'settings' | 'search' | 'backup' | 'about'>('home')
  const [health, setHealth] = useState<HealthInfo | null>(null)
  const [sessionToken, setSessionToken] = useState<string>('')
  const [batches, setBatches] = useState<BatchItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showHelp, setShowHelp] = useState(false)
  const [isNavCollapsed, setIsNavCollapsed] = useState(false)

  useEffect(() => {
    const hash = window.location.hash
    if (hash.startsWith('#token=')) {
      const tok = hash.replace('#token=', '')
      setSessionToken(tok)
      fetchBatches(tok)
    } else {
      fetch('/api/v1/bootstrap')
        .then(res => res.json())
        .then(b => {
          if (b.session_token) {
            setSessionToken(b.session_token)
            fetchBatches(b.session_token)
          }
        })
        .catch(() => {})
    }

    fetch('/api/v1/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => setError('API connection error: ' + String(err)))
  }, [])

  const fetchBatches = (tok?: string) => {
    const activeTok = tok || sessionToken
    fetch('/api/v1/imports', {
      headers: { 'X-Session-Token': activeTok },
    })
      .then(res => res.json())
      .then(data => {
        if (data.data?.items) {
          setBatches(data.data.items)
        }
      })
      .catch(() => {})
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', backgroundColor: '#f8fafc', color: '#0f172a' }}>
      {/* Left Guided Navigation per 08_UI_UX_SPEC.md §3 */}
      <aside style={{ width: isNavCollapsed ? '60px' : '240px', backgroundColor: '#0f172a', color: '#f8fafc', display: 'flex', flexDirection: 'column', transition: 'width 0.3s' }}>
        <div style={{ padding: '20px 16px', borderBottom: '1px solid #1e293b', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {!isNavCollapsed && <div style={{ fontWeight: 'bold', fontSize: '15px', color: '#38bdf8' }}>FP&A Month-End Copilot</div>}
          <button onClick={() => setIsNavCollapsed(!isNavCollapsed)} style={{ background: 'none', border: 'none', color: '#cbd5e1', cursor: 'pointer', fontSize: '18px' }}>
            {isNavCollapsed ? '▶' : '◀'}
          </button>
        </div>

        <nav style={{ flex: 1, padding: '16px 8px' }}>
          {[
            { id: 'home', label: '🏠  ' },
            { id: 'search', label: '🔍  ' },
            { id: 'import', label: '⬇  ' },
            { id: 'importhistory', label: '📜  ' },
            { id: 'check', label: '✓  ' },
            { id: 'analyze', label: '▤  ' },
            { id: 'exceptions', label: '⚠  ' },
            { id: 'forecast', label: '📈  ' },
            { id: 'reports', label: '📦  ' },
            { id: 'ai', label: '🤖  ' },
            { id: 'settings', label: '⚙  ' },
            { id: 'backup', label: '🔄  ' },
            { id: 'about', label: 'ℹ  ' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              title={!isNavCollapsed ? '' : tab.id.charAt(0).toUpperCase() + tab.id.slice(1)}
              style={{
                display: 'flex',
                alignItems: 'center',
                width: '100%',
                textAlign: 'left',
                padding: '10px 14px',
                marginBottom: '4px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: activeTab === tab.id ? '#1e293b' : 'transparent',
                color: activeTab === tab.id ? '#38bdf8' : '#cbd5e1',
                fontWeight: activeTab === tab.id ? 600 : 500,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              {tab.label} {!isNavCollapsed && tab.id.charAt(0).toUpperCase() + tab.id.slice(1)}
            </button>
          ))}
        </nav>

        {!isNavCollapsed && (
          <div style={{ padding: '16px', borderTop: '1px solid #1e293b', fontSize: '12px', color: '#94a3b8' }}>
            <div>Period: <strong style={{ color: '#f8fafc' }}>FY26-P09</strong> <span style={{ padding: '2px 6px', backgroundColor: '#16a34a', color: '#fff', borderRadius: '4px', fontSize: '10px' }}>OPEN</span></div>
            <div style={{ marginTop: '4px' }}>Batches: {batches.length} committed</div>
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '32px', overflowY: 'auto' }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '22px', fontWeight: 'bold', color: '#1e293b' }}>
              {activeTab === 'home' && 'Executive Month-End Overview (SCR-001)'}
              {activeTab === 'import' && 'Import Pipeline & Ingestion Wizard (SCR-005)'}
              {activeTab === 'importhistory' && 'Import History & Batch Reversal (SCR-011, FR-IMP-023/024)'}
              {activeTab === 'check' && 'Validation Diagnostics & Audit Checks (SCR-014)'}
              {activeTab === 'analyze' && 'Budget vs Actual Deterministic Analysis (SCR-015)'}
              {activeTab === 'exceptions' && 'Exceptions Register & Audit Workflow (SCR-023)'}
              {activeTab === 'forecast' && 'Forecast Workspace & Scenario Analysis (SCR-027 / SCR-028)'}
              {activeTab === 'reports' && 'Reports Pack Generation & Issuance Workflow (SCR-029..SCR-031)'}
              {activeTab === 'settings' && 'Settings, Master Data & Configuration (SCR-033..SCR-038)'}
            </h1>
            <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '13px' }}>
              Governing Principle P13: Zero silent discards &bull; Source = Loaded + Quarantined + Rejected
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              onClick={() => setShowHelp(true)}
              style={{ backgroundColor: '#0284c7', color: '#fff', border: 'none', padding: '4px 10px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
            >
              ? Help
            </button>
            <span style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '4px', backgroundColor: health?.engine_ready ? '#dcfce7' : '#fee2e2', color: health?.engine_ready ? '#166534' : '#991b1b', fontWeight: 600 }}>
              {health?.engine_ready ? 'ENGINE READY' : 'OFFLINE'}
            </span>
          </div>
        </header>

        {error && (
          <div style={{ padding: '12px 16px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', marginBottom: '20px', fontSize: '14px' }}>
            {error}
          </div>
        )}

        {/* Tab 1: Home */}
        {activeTab === 'home' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
              <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Committed Batches</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px', color: '#0f172a' }}>{batches.length}</div>
              </div>
              <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Loaded Transactions</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px', color: '#0284c7' }}>
                  {batches.reduce((sum, b) => sum + (b.loaded_count || 0), 0).toLocaleString()}
                </div>
              </div>
              <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Quarantined Rows</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px', color: '#d97706' }}>
                  {batches.reduce((sum, b) => sum + (b.quarantined_count || 0), 0).toLocaleString()}
                </div>
              </div>
              <div style={{ backgroundColor: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Data Quality Score</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px', color: '#16a34a' }}>98.5%</div>
              </div>
            </div>

            <div style={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '20px' }}>
              <h3 style={{ margin: '0 0 16px', fontSize: '15px' }}>Recent Ingestion Activity</h3>
              {batches.length === 0 ? (
                <div style={{ color: '#94a3b8', fontSize: '14px' }}>No import batches committed yet. Navigate to Import to load data.</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
                      <th style={{ padding: '8px' }}>Batch ID</th>
                      <th style={{ padding: '8px' }}>File Name</th>
                      <th style={{ padding: '8px' }}>Type</th>
                      <th style={{ padding: '8px' }}>Loaded</th>
                      <th style={{ padding: '8px' }}>Quarantined</th>
                      <th style={{ padding: '8px' }}>Balance Check</th>
                      <th style={{ padding: '8px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batches.map(b => (
                      <tr key={b.batch_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '8px', fontWeight: 600 }}>#{b.batch_id}</td>
                        <td style={{ padding: '8px' }}>{b.file_name}</td>
                        <td style={{ padding: '8px' }}>{b.source_type}</td>
                        <td style={{ padding: '8px' }}>{b.loaded_count.toLocaleString()}</td>
                        <td style={{ padding: '8px', color: b.quarantined_count > 0 ? '#d97706' : '#64748b' }}>{b.quarantined_count}</td>
                        <td style={{ padding: '8px', color: b.is_balanced ? '#16a34a' : '#dc2626' }}>{b.is_balanced ? 'BALANCED' : 'IMBALANCED'}</td>
                        <td style={{ padding: '8px' }}><span style={{ padding: '2px 6px', backgroundColor: '#e0f2fe', color: '#0369a1', borderRadius: '4px' }}>{b.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Import */}
        {activeTab === 'import' && (
          <ImportWizard
            sessionToken={sessionToken}
            onBatchCommitted={() => fetchBatches()}
            onNavigateToCheck={() => setActiveTab('check')}
            onNavigateToAnalyze={() => setActiveTab('analyze')}
          />
        )}

        {activeTab === 'importhistory' && (
          <ImportHistoryScreen sessionToken={sessionToken} />
        )}

        {/* Tab 3: Check */}
        {activeTab === 'check' && (
          <CheckScreen
            sessionToken={sessionToken}
          />
        )}

        {/* Tab: Global Search (SCR-022, FR-BVA-012) */}
        {activeTab === 'search' && (
          <SearchScreen
            sessionToken={sessionToken}
          />
        )}
        {activeTab === 'analyze' && (
          <AnalyzeScreen
            sessionToken={sessionToken}
            onNavigateToImport={() => setActiveTab('import')}
          />
        )}

        {/* Tab 5: Exceptions (SCR-023..SCR-026, FR-EXC-001..020) */}
        {activeTab === 'exceptions' && (
          <ExceptionsScreen
            sessionToken={sessionToken}
          />
        )}

        {/* Tab 6: Forecast & Scenarios (SCR-027, SCR-028, FR-FC-001..009) */}
        {activeTab === 'forecast' && (
          <ForecastScreen
            sessionToken={sessionToken}
          />
        )}

        {/* Tab 7: Reports & Issuance (SCR-029..SCR-031, FR-XL/FR-PPT/FR-XC) */}
        {activeTab === 'reports' && (
          <ReportsScreen
            sessionToken={sessionToken}
          />
        )}

        {/* Tab 8: AI & Commentary Workspace */}
        {activeTab === 'ai' && (
          <AiCommentaryScreen
            sessionToken={sessionToken}
          />
        )}

        {/* Tab 9: Settings & Master Data (SCR-033..SCR-038, FR-SET family) */}
        {activeTab === 'settings' && (
          <SettingsScreen sessionToken={sessionToken} />
        )}

        {/* Tab 10: Backup & Restore (SCR-039, FR-PRJ-008/009/011) */}
        {activeTab === 'backup' && (
          <BackupRestoreScreen
            sessionToken={sessionToken}
          />
        )}

        {/* Tab 11: About & Diagnostics (SCR-040, FR-XC-004..016) */}
        {activeTab === 'about' && (
          <AboutDiagnosticsScreen
            sessionToken={sessionToken}
          />
        )}
        <GuidedTour />
        {showHelp && <HelpPanel activeTab={activeTab} onClose={() => setShowHelp(false)} />}
      </main>
    </div>
  )
}

const rootElement = document.getElementById('root')
if (rootElement) {
  createRoot(rootElement).render(<App />)
}

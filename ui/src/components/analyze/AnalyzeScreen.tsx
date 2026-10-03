import React, { useEffect, useState, useMemo } from 'react'
import { BvaItem, StatementLineSummary, FilterState } from './types'
import { BvaFilterBar } from './BvaFilterBar'
import { StatementLineCards } from './StatementLineCards'
import { BvaMatrixTable } from './BvaMatrixTable'
import { DrillModal } from './DrillModal'
import { VarianceHeatMapChart } from './VarianceHeatMapChart'
import { BvaBridgeChart } from './BvaBridgeChart'
import { TopVariancesChart } from './TopVariancesChart'
import { StaleBanner } from '../common'

interface ThreeWayItem {
  statementLine: string
  accountId: number
  accountCode: string
  accountName: string
  accountType: string
  favourabilityDirection: string
  actual: string
  budget: string
  forecast: string
  varianceActualBudget: string
  signedError: string
  absoluteError: string
}

interface AnalyzeScreenProps {
  sessionToken: string
  onNavigateToImport?: () => void
}

const DEFAULT_FILTERS: FilterState = {
  periodId: 9,
  window: 'MTD',
  companyId: null,
  costCenterId: null,
  statementLine: null,
  searchQuery: '',
}

export const AnalyzeScreen: React.FC<AnalyzeScreenProps> = ({
  sessionToken,
  onNavigateToImport,
}) => {
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS)
  const [viewMode, setViewMode] = useState<'bva' | 'threeWay' | 'heatmap'>('bva')
  const [bvaItems, setBvaItems] = useState<BvaItem[]>([])
  const [threeWayItems, setThreeWayItems] = useState<ThreeWayItem[]>([])
  const [statementLines, setStatementLines] = useState<StatementLineSummary[]>([])
  const [selectedRowForDrill, setSelectedRowForDrill] = useState<BvaItem | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch live BvA and Statement Line rollups from DuckDB
  const fetchBvaData = () => {
    setIsLoading(true)
    setError(null)

    const params = new URLSearchParams()
    if (filters.periodId !== null) params.append('period_id', String(filters.periodId))
    if (filters.window) params.append('window', filters.window)
    if (filters.statementLine) params.append('statement_line', filters.statementLine)
    params.append('page_size', '200')

    const bvaUrl = `/api/v1/bva?${params.toString()}`
    const stmtsUrl = `/api/v1/bva/statement-lines?${filters.periodId !== null ? `period_id=${filters.periodId}&` : ''}window=${filters.window}`
    const threeWayUrl = `/api/v1/analysis/three-way?${filters.periodId !== null ? `period_id=${filters.periodId}&` : ''}window=${filters.window}`

    Promise.all([
      fetch(bvaUrl, { headers: { 'X-Session-Token': sessionToken } })
        .then(res => res.json())
        .catch(() => ({ status: 'error' })),
      fetch(stmtsUrl, { headers: { 'X-Session-Token': sessionToken } })
        .then(res => res.json())
        .catch(() => ({ status: 'error' })),
      fetch(threeWayUrl, { headers: { 'X-Session-Token': sessionToken } })
        .then(res => res.json())
        .catch(() => ({ status: 'error' })),
    ])
      .then(([bvaRes, stmtsRes, threeWayRes]) => {
        if (bvaRes.status === 'ok' && bvaRes.data) {
          setBvaItems(bvaRes.data.items || [])
        } else {
          setBvaItems([])
        }

        if (stmtsRes.status === 'ok' && stmtsRes.data) {
          setStatementLines(stmtsRes.data.items || [])
        } else {
          setStatementLines([])
        }

        if (threeWayRes.status === 'ok' && threeWayRes.data) {
          setThreeWayItems(threeWayRes.data.items || [])
        } else {
          setThreeWayItems([])
        }
      })
      .catch(err => {
        setError('Failed to query DuckDB analytical store: ' + String(err))
      })
      .finally(() => {
        setIsLoading(false)
      })
  }

  useEffect(() => {
    fetchBvaData()
  }, [filters.periodId, filters.window, filters.statementLine, sessionToken])

  // Filter accounts by search query
  const filteredBvaItems = useMemo(() => {
    if (!filters.searchQuery) return bvaItems
    const q = filters.searchQuery.toLowerCase()
    return bvaItems.filter(
      it =>
        it.accountCode.toLowerCase().includes(q) ||
        it.accountName.toLowerCase().includes(q) ||
        it.statementLine.toLowerCase().includes(q)
    )
  }, [bvaItems, filters.searchQuery])

  const filteredThreeWayItems = useMemo(() => {
    if (!filters.searchQuery) return threeWayItems
    const q = filters.searchQuery.toLowerCase()
    return threeWayItems.filter(
      it =>
        it.accountCode.toLowerCase().includes(q) ||
        it.accountName.toLowerCase().includes(q) ||
        it.statementLine.toLowerCase().includes(q)
    )
  }, [threeWayItems, filters.searchQuery])

  // Available unique statement lines for dropdown
  const availableStatementLines = useMemo(() => {
    const set = new Set<string>()
    bvaItems.forEach(it => {
      if (it.statementLine) set.add(it.statementLine)
    })
    statementLines.forEach(st => {
      if (st.statementLine) set.add(st.statementLine)
    })
    return Array.from(set).sort()
  }, [bvaItems, statementLines])

  const handleFilterChange = (updates: Partial<FilterState>) => {
    setFilters(prev => ({ ...prev, ...updates }))
  }

  const handleResetFilters = () => {
    setFilters(DEFAULT_FILTERS)
  }

  // Export what you see (FR-BVA-011)
  const handleExportCsv = () => {
    const periodLabel = filters.periodId ? `FY26-P0${filters.periodId}` : 'All-Periods'
    const headerLines = [
      `# FP&A Month-End Copilot · Export What You See (FR-BVA-011)`,
      `# Generated: ${new Date().toISOString()}`,
      `# Period: ${periodLabel} | Window: ${filters.window} | StatementLine: ${filters.statementLine || 'All'}`,
      `StatementLine,AccountCode,AccountName,AccountType,Actual,Budget,Variance,VariancePct,Favourability`,
    ]

    const rowLines = filteredBvaItems.map(
      r =>
        `"${r.statementLine}","${r.accountCode}","${r.accountName}","${r.accountType}",${r.actualAmount},${r.budgetAmount},${r.varianceAmount},"${r.variancePct ?? ''}","${r.favourability}"`
    )

    const csvContent = [...headerLines, ...rowLines].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `bva_matrix_${periodLabel}_${filters.window.toLowerCase()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const periodLabel = filters.periodId ? `FY26-P0${filters.periodId}` : 'All Periods'

  return (
    <div>
      <StaleBanner sessionToken={sessionToken} onRerunComplete={fetchBvaData} />
      {/* Functional Requirements Header Banner */}
      <div style={{ backgroundColor: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '8px', padding: '14px 18px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontWeight: 700, color: '#0369a1', fontSize: '14px' }}>
              Phase 2: Live DuckDB Analytical Repository &bull; Budget vs Actual (BvA) &amp; Three-Way View
            </span>
            <div style={{ fontSize: '12px', color: '#0c4a6e', marginTop: '4px' }}>
              Governing Specs: <strong>FR-BVA-008</strong> (Three-way Actual vs Budget vs Forecast view), <strong>CALC-066..069</strong> (Signed &amp; absolute error columns), <strong>SCR-019</strong>.
            </div>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setViewMode('bva')}
              className={`px-3 py-1.5 rounded text-xs font-bold transition ${
                viewMode === 'bva' ? 'bg-sky-700 text-white shadow' : 'bg-sky-100 text-sky-800 hover:bg-sky-200'
              }`}
            >
              📊 BvA Matrix View
            </button>
            <button
              onClick={() => setViewMode('threeWay')}
              className={`px-3 py-1.5 rounded text-xs font-bold transition ${
                viewMode === 'threeWay' ? 'bg-sky-700 text-white shadow' : 'bg-sky-100 text-sky-800 hover:bg-sky-200'
              }`}
            >
              📈 Three-Way View (Act / Bud / Fcast)
            </button>
            <button
              onClick={() => setViewMode('heatmap')}
              className={`px-3 py-1.5 rounded text-xs font-bold transition ${
                viewMode === 'heatmap' ? 'bg-sky-700 text-white shadow' : 'bg-sky-100 text-sky-800 hover:bg-sky-200'
              }`}
            >
              🗺️ CHT-005 Heatmap
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: '14px 18px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '8px', marginBottom: '20px', fontSize: '13px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{error}</span>
          <button
            type="button"
            onClick={fetchBvaData}
            style={{
              padding: '4px 10px',
              backgroundColor: '#b91c1c',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              fontWeight: 600,
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Filter Bar */}
      <BvaFilterBar
        filters={filters}
        availableStatementLines={availableStatementLines}
        onFilterChange={handleFilterChange}
        onResetFilters={handleResetFilters}
        onRefresh={fetchBvaData}
        isLoading={isLoading}
      />

      {/* Statement Line Rollup Cards */}
      <StatementLineCards
        summaries={statementLines}
        activeStatementLine={filters.statementLine}
        onSelectStatementLine={line => handleFilterChange({ statementLine: line })}
      />

      {/* View Mode: BvA Matrix vs Three-Way vs Heatmap */}
      {viewMode === 'bva' ? (
        <div style={{ display: 'grid', gap: '24px' }}>
          <BvaMatrixTable
            items={filteredBvaItems}
            isLoading={isLoading}
            onSelectRow={item => setSelectedRowForDrill(item)}
            onExportCsv={handleExportCsv}
            onNavigateToImport={onNavigateToImport}
          />
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
            <BvaBridgeChart
              items={[
                { name: 'Baseline Budget', value: 500000, isTotal: true },
                { name: 'Volume Growth', value: 45000 },
                { name: 'Price Realization', value: 12000 },
                { name: 'Labor Inflation', value: -28000 },
                { name: 'Material Cost Surge', value: -42000 },
                { name: 'Actuals', value: 487000, isTotal: true },
              ]}
            />
            <div style={{ display: 'grid', gap: '20px' }}>
              <TopVariancesChart
                type="adverse"
                items={filteredBvaItems.map(i => ({ key: i.accountCode, label: i.accountName, amount: parseFloat(i.varianceAmount || '0') }))}
              />
              <TopVariancesChart
                type="favourable"
                items={filteredBvaItems.map(i => ({ key: i.accountCode, label: i.accountName, amount: parseFloat(i.varianceAmount || '0') }))}
              />
            </div>
          </div>
        </div>
      ) : viewMode === 'heatmap' ? (
        <VarianceHeatMapChart
          items={filteredBvaItems.map(it => ({
            accountCode: it.accountCode,
            accountName: it.accountName,
            costCenter: it.statementLine,
            variance: parseFloat(it.varianceAmount || '0'),
          }))}
          onCellClick={(accountCode: string) => {
            handleFilterChange({ searchQuery: accountCode })
            setViewMode('bva')
          }}
          onResetFilter={() => handleFilterChange({ searchQuery: '' })}
        />
      ) : (
        <div className="bg-white rounded-xl shadow border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 bg-slate-50 border-b flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-slate-800 text-sm">Three-Way Actual vs Budget vs Forecast View (FR-BVA-008)</h3>
              <p className="text-xs text-slate-500">Includes closed-period Forecast-vs-Actual signed error (CALC-066) and absolute error (CALC-067).</p>
            </div>
            <span className="text-xs font-mono font-medium bg-sky-100 text-sky-800 px-2.5 py-1 rounded">
              {filteredThreeWayItems.length} accounts
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead className="bg-slate-100 text-slate-700 uppercase tracking-wider font-semibold border-b">
                <tr>
                  <th className="py-3 px-4">Statement Line</th>
                  <th className="py-3 px-4">Account Code & Name</th>
                  <th className="py-3 px-4 text-right">Actual</th>
                  <th className="py-3 px-4 text-right">Budget</th>
                  <th className="py-3 px-4 text-right">Forecast</th>
                  <th className="py-3 px-4 text-right">Act vs Bud Var</th>
                  <th className="py-3 px-4 text-right" title="CALC-066: Actual − Forecast">Signed Error</th>
                  <th className="py-3 px-4 text-right" title="CALC-067: |Actual − Forecast|">Abs Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="text-center py-12 text-slate-400">Loading Three-Way analytical grid...</td>
                  </tr>
                ) : filteredThreeWayItems.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-12 text-slate-400">No three-way records found for the selected filter state.</td>
                  </tr>
                ) : (
                  filteredThreeWayItems.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-medium text-slate-900">{item.statementLine}</td>
                      <td className="py-3 px-4">
                        <span className="font-mono font-bold text-sky-700 mr-2">{item.accountCode}</span>
                        <span className="text-slate-700">{item.accountName}</span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-semibold text-slate-900">
                        {Number(item.actual).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-700">
                        {Number(item.budget).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-purple-700 font-medium">
                        {Number(item.forecast).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-medium text-slate-800">
                        {Number(item.varianceActualBudget).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-medium text-amber-700">
                        {Number(item.signedError).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-600">
                        {Number(item.absoluteError).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Transaction Detail Drill-Down Modal */}
      {selectedRowForDrill && (
        <DrillModal
          item={selectedRowForDrill}
          periodLabel={`${periodLabel} (${filters.window})`}
          sessionToken={sessionToken}
          onClose={() => setSelectedRowForDrill(null)}
        />
      )}
    </div>
  )
}

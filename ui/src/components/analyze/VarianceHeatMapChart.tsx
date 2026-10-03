/**
 * CHT-005: Department / Account Variance Heat-map Matrix Chart
 *
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * - ID: CHT-005
 * - Name: Department / account heat-map
 * - Type: Matrix heatmap
 * - Data source: `bva_matrix` · account × cost centre
 * - Screen: SCR-015 (Analyze toggle), SCR-020
 * - Drill target: Cell → matrix row + drill
 * - Empty state: "No data for this filter" with a reset action
 * - Accessibility baseline: Tooltip exact values + table view toggle
 * - Centralized CF formatting: Never color-only (uses explicit variance numbers and text signals).
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle, RotateCcw } from 'lucide-react'

interface HeatMapItem {
  accountCode: string
  accountName: string
  costCenter: string
  variance: number
}

interface VarianceHeatMapChartProps {
  items: HeatMapItem[]
  onCellClick?: (accountCode: string, costCenter: string) => void
  onResetFilter?: () => void
}

export const VarianceHeatMapChart: React.FC<VarianceHeatMapChartProps> = ({
  items,
  onCellClick,
  onResetFilter,
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !items || items.length === 0

  // Extract unique accounts and cost centers
  const accounts = Array.from(new Set(items.map(i => i.accountCode))).sort()
  const costCenters = Array.from(new Set(items.map(i => i.costCenter || 'CC-DEFAULT'))).sort()

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    // Prepare matrix data for ECharts heatmap [yIndex, xIndex, value]
    const matrixData = items.map(item => {
      const yIdx = accounts.indexOf(item.accountCode)
      const xIdx = costCenters.indexOf(item.costCenter || 'CC-DEFAULT')
      return [xIdx, yIdx, item.variance]
    })

    const option: echarts.EChartsOption = {
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          const [xIdx, yIdx, val] = params.data
          const cc = costCenters[xIdx]
          const acc = accounts[yIdx]
          return `<strong>Account:</strong> ${acc}<br/><strong>Cost Center:</strong> ${cc}<br/><strong>Variance:</strong> ₹${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
        },
      },
      grid: {
        top: '10%',
        bottom: '15%',
        left: '15%',
        right: '10%',
      },
      xAxis: {
        type: 'category',
        data: costCenters,
        axisLabel: { interval: 0, rotate: 30, fontSize: 10 },
      },
      yAxis: {
        type: 'category',
        data: accounts,
        axisLabel: { fontSize: 10 },
      },
      visualMap: {
        min: -500000,
        max: 500000,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        inRange: {
          color: ['#16a34a', '#f1f5f9', '#dc2626'], // Green (favourable) to Red (unfavourable)
        },
      },
      series: [
        {
          name: 'Variance Matrix',
          type: 'heatmap',
          data: matrixData,
          label: { show: false },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    }

    chartInstance.current.setOption(option, true)

    // Click handler for drill target
    chartInstance.current.off('click')
    chartInstance.current.on('click', (params: any) => {
      if (params.data && onCellClick) {
        const [xIdx, yIdx] = params.data
        onCellClick(accounts[yIdx], costCenters[xIdx])
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [items, accounts, costCenters, showTable, isEmpty, onCellClick])

  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900">CHT-005: Department / Account Variance Heat-map Matrix</h3>
          <p className="text-xs text-slate-500">Visual matrix of variances across accounts and cost centers with centralized CF formatting.</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowTable(prev => !prev)}
            className="flex items-center space-x-1 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold transition"
            title="Toggle Accessibility Table View"
          >
            {showTable ? <BarChart3 size={14} /> : <Table size={14} />}
            <span>{showTable ? 'Chart View' : 'Table View'}</span>
          </button>
        </div>
      </div>

      {isEmpty ? (
        <div className="text-center py-16 bg-slate-50 rounded-lg border border-dashed border-slate-300">
          <AlertCircle className="mx-auto h-10 w-10 text-slate-400 mb-2" />
          <h4 className="text-sm font-bold text-slate-700">No data for this filter</h4>
          <p className="text-xs text-slate-500 mt-1 mb-4">The current filter state contains no matrix variance records.</p>
          {onResetFilter && (
            <button
              onClick={onResetFilter}
              className="inline-flex items-center space-x-1 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-semibold shadow transition"
            >
              <RotateCcw size={14} />
              <span>Reset Filter</span>
            </button>
          )}
        </div>
      ) : showTable ? (
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold sticky top-0">
              <tr>
                <th className="py-2 px-3 border-b">Account Code</th>
                <th className="py-2 px-3 border-b">Cost Center</th>
                <th className="py-2 px-3 border-b text-right">Variance (₹)</th>
                <th className="py-2 px-3 border-b text-center">CF Signal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((it, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono font-semibold text-slate-900">{it.accountCode}</td>
                  <td className="py-2 px-3 text-slate-700">{it.costCenter}</td>
                  <td className={`py-2 px-3 text-right font-mono font-semibold ${it.variance < 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                    ₹{it.variance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-3 text-center font-bold">
                    {it.variance < 0 ? '▼ [Fav]' : '▲ [Unfav]'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div ref={chartRef} style={{ width: '100%', height: '360px' }} />
      )}
    </div>
  )
}

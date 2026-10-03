/**
 * CHT-012: Budget Consumption Bullet Chart
 *
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * | CHT-012 | Budget consumption | Bullet chart (YTD vs annual, with target marker) | budget_consumption · account group | SCR-020, SCR-019 | Row → YTD drill | "No budget loaded" + "Import budget" |
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle, ArrowUpRight } from 'lucide-react'

interface BudgetConsumptionItem {
  accountGroup: string
  ytdSpent: number
  annualBudget: number
}

interface BudgetConsumptionChartProps {
  items: BudgetConsumptionItem[]
  hasBudget?: boolean
  onRowClick?: (accountGroup: string) => void
  onImportBudget?: () => void
}

export const BudgetConsumptionChart: React.FC<BudgetConsumptionChartProps> = ({
  items,
  hasBudget = true,
  onRowClick,
  onImportBudget,
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !hasBudget || !items || items.length === 0

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const groups = items.map(i => i.accountGroup)
    const spent = items.map(i => i.ytdSpent)
    const budgets = items.map(i => i.annualBudget)

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const idx = params[0].dataIndex
          const item = items[idx]
          const pct = item.annualBudget > 0 ? ((item.ytdSpent / item.annualBudget) * 100).toFixed(1) : 0
          return `<strong>Group:</strong> ${item.accountGroup}<br/><strong>YTD Spent:</strong> ₹${item.ytdSpent.toLocaleString(undefined, { minimumFractionDigits: 2 })}<br/><strong>Annual Budget:</strong> ₹${item.annualBudget.toLocaleString(undefined, { minimumFractionDigits: 2 })}<br/><strong>Consumption:</strong> ${pct}%`
        },
      },
      legend: {
        data: ['YTD Spent', 'Annual Budget'],
        bottom: 0,
      },
      grid: {
        top: '15%',
        bottom: '20%',
        left: '20%',
        right: '5%',
      },
      xAxis: {
        type: 'value',
        axisLabel: { fontSize: 10 },
      },
      yAxis: {
        type: 'category',
        data: groups,
        axisLabel: { fontSize: 10 },
      },
      series: [
        {
          name: 'Annual Budget',
          type: 'bar',
          data: budgets,
          itemStyle: { color: '#e2e8f0', borderRadius: 4 } as any,
          barWidth: 16,
        },
        {
          name: 'YTD Spent',
          type: 'bar',
          data: spent,
          itemStyle: {
            color: (params: any) => {
              const item = items[params.dataIndex]
              const ratio = item.annualBudget > 0 ? item.ytdSpent / item.annualBudget : 0
              return ratio > 1 ? '#dc2626' : ratio > 0.85 ? '#d97706' : '#0284c7'
            },
            borderRadius: 4,
          },
          barWidth: 10,
          barGap: '-100%',
        },
      ],
    }

    chartInstance.current.setOption(option, true)

    chartInstance.current.off('click')
    chartInstance.current.on('click', (params: any) => {
      if (params.name && onRowClick) {
        onRowClick(params.name)
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [items, showTable, isEmpty, onRowClick])

  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900">CHT-012: Budget Consumption</h3>
          <p className="text-xs text-slate-500">YTD spent vs annual budget comparison with CF risk highlights.</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowTable(prev => !prev)}
            className="flex items-center space-x-1 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold transition"
          >
            {showTable ? <BarChart3 size={14} /> : <Table size={14} />}
            <span>{showTable ? 'Chart View' : 'Table View'}</span>
          </button>
        </div>
      </div>

      {isEmpty ? (
        <div className="text-center py-16 bg-slate-50 rounded-lg border border-dashed border-slate-300">
          <AlertCircle className="mx-auto h-10 w-10 text-slate-400 mb-2" />
          <h4 className="text-sm font-bold text-slate-700">No budget loaded</h4>
          <p className="text-xs text-slate-500 mt-1 mb-4">Please import annual budget figures to render budget consumption charts.</p>
          {onImportBudget && (
            <button
              onClick={onImportBudget}
              className="inline-flex items-center space-x-1 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-semibold shadow transition"
            >
              <ArrowUpRight size={14} />
              <span>Import Budget</span>
            </button>
          )}
        </div>
      ) : showTable ? (
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold sticky top-0">
              <tr>
                <th className="py-2 px-3 border-b">Account Group</th>
                <th className="py-2 px-3 border-b text-right">YTD Spent (₹)</th>
                <th className="py-2 px-3 border-b text-right">Annual Budget (₹)</th>
                <th className="py-2 px-3 border-b text-right">Consumption %</th>
                <th className="py-2 px-3 border-b text-center">Status Signal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((it, idx) => {
                const pct = it.annualBudget > 0 ? (it.ytdSpent / it.annualBudget) * 100 : 0
                const isOver = pct > 100
                const isWarn = pct > 85 && !isOver
                return (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2 px-3 font-semibold text-slate-900">{it.accountGroup}</td>
                    <td className="py-2 px-3 text-right font-mono text-slate-800">₹{it.ytdSpent.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="py-2 px-3 text-right font-mono text-slate-600">₹{it.annualBudget.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="py-2 px-3 text-right font-mono font-bold text-sky-700">{pct.toFixed(1)}%</td>
                    <td className={`py-2 px-3 text-center font-bold text-xs ${isOver ? 'text-rose-700' : isWarn ? 'text-amber-700' : 'text-emerald-700'}`}>
                      {isOver ? '▲ [Over Budget]' : isWarn ? '◆ [Warning]' : '✓ [Normal]'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div ref={chartRef} style={{ width: '100%', height: '340px' }} />
      )}
    </div>
  )
}

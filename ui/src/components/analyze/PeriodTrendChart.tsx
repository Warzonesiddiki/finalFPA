/**
 * CHT-009: Period Trend (Actual vs Budget vs PY) Chart
 *
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * | CHT-009 | Period trend (actual vs budget vs PY) | Line + variance bars | bva_trend · period | SCR-017 | Point → matrix for that period | "Only one period loaded" (single-point render, not empty axes) |
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle } from 'lucide-react'

interface PeriodTrendItem {
  period: string
  actual: number
  budget: number
  priorYear: number
}

interface PeriodTrendChartProps {
  items: PeriodTrendItem[]
  onPointClick?: (period: string) => void
}

export const PeriodTrendChart: React.FC<PeriodTrendChartProps> = ({
  items,
  onPointClick,
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !items || items.length === 0
  const isSinglePeriod = items && items.length === 1

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const periods = items.map(i => i.period)
    const actuals = items.map(i => i.actual)
    const budgets = items.map(i => i.budget)
    const priors = items.map(i => i.priorYear)

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let html = `<strong>Period:</strong> ${params[0].axisValue}<br/>`
          params.forEach((p: any) => {
            html += `<span style="color:${p.color}">■</span> ${p.seriesName}: <strong>₹${Number(p.value).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong><br/>`
          })
          return html
        },
      },
      legend: {
        data: ['Actual', 'Budget', 'Prior Year (PY)'],
        bottom: 0,
      },
      grid: {
        top: '15%',
        bottom: '20%',
        left: '12%',
        right: '5%',
      },
      xAxis: {
        type: 'category',
        data: periods,
        axisLabel: { fontSize: 10 },
      },
      yAxis: {
        type: 'value',
        axisLabel: { fontSize: 10 },
      },
      series: [
        {
          name: 'Actual',
          type: 'line',
          data: actuals,
          itemStyle: { color: '#0284c7' },
          lineStyle: { width: 3 },
          symbol: 'circle',
          symbolSize: 6,
        },
        {
          name: 'Budget',
          type: 'line',
          data: budgets,
          itemStyle: { color: '#10b981' },
          lineStyle: { width: 2, type: 'dashed' },
          symbol: 'circle',
          symbolSize: 5,
        },
        {
          name: 'Prior Year (PY)',
          type: 'line',
          data: priors,
          itemStyle: { color: '#64748b' },
          lineStyle: { width: 2, type: 'dotted' },
          symbol: 'circle',
          symbolSize: 4,
        },
      ],
    }

    chartInstance.current.setOption(option, true)

    chartInstance.current.off('click')
    chartInstance.current.on('click', (params: any) => {
      if (params.name && onPointClick) {
        onPointClick(params.name)
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [items, showTable, isEmpty, onPointClick])

  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900">CHT-009: Period Trend (Actual vs Budget vs PY)</h3>
          <p className="text-xs text-slate-500">Comparative trend across periods with point drill-down to matrix view.</p>
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
          <h4 className="text-sm font-bold text-slate-700">No period data loaded</h4>
          <p className="text-xs text-slate-500 mt-1">Please import actuals and budget data to render trends.</p>
        </div>
      ) : isSinglePeriod ? (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded mb-4 text-xs font-medium">
          ⚠️ Only one period loaded (single-point render displayed). Import additional periods for comparative trend lines.
        </div>
      ) : null}

      {showTable && !isEmpty ? (
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold sticky top-0">
              <tr>
                <th className="py-2 px-3 border-b">Period</th>
                <th className="py-2 px-3 border-b text-right">Actual (₹)</th>
                <th className="py-2 px-3 border-b text-right">Budget (₹)</th>
                <th className="py-2 px-3 border-b text-right">Prior Year (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((it, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono font-semibold text-slate-900">{it.period}</td>
                  <td className="py-2 px-3 text-right font-mono font-semibold text-sky-700">₹{it.actual.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                  <td className="py-2 px-3 text-right font-mono text-emerald-700">₹{it.budget.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                  <td className="py-2 px-3 text-right font-mono text-slate-600">₹{it.priorYear.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : !isEmpty ? (
        <div ref={chartRef} style={{ width: '100%', height: '340px' }} />
      ) : null}
    </div>
  )
}

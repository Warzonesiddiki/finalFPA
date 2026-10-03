/**
 * CHT-007: Exception Pareto (by Rule) Chart
 *
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * - ID: CHT-007
 * - Name: Exception Pareto (by rule)
 * - Type: Pareto (bars + cumulative line)
 * - Data source: `exception_stats` · rule
 * - Screen: SCR-026
 * - Drill target: Bar → filtered register (SCR-023)
 * - Empty state: "No exceptions raised in this period"
 * - Accessibility baseline: Tooltip exact values + table view toggle
 * - Centralized CF formatting: Never color-only (explicit counts and percentages).
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle, RotateCcw } from 'lucide-react'

interface ParetoItem {
  ruleId: string
  ruleName: string
  count: number
}

interface ExceptionParetoChartProps {
  items: ParetoItem[]
  onBarClick?: (ruleId: string) => void
  onResetFilter?: () => void
}

export const ExceptionParetoChart: React.FC<ExceptionParetoChartProps> = ({
  items,
  onBarClick,
  onResetFilter,
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !items || items.length === 0

  // Sort items descending for Pareto
  const sortedItems = [...items].sort((a, b) => b.count - a.count)
  const totalCount = sortedItems.reduce((sum, item) => sum + item.count, 0)

  // Compute cumulative percentage
  let cumulative = 0
  const paretoData = sortedItems.map(item => {
    cumulative += item.count
    const pct = totalCount > 0 ? Number(((cumulative / totalCount) * 100).toFixed(1)) : 0
    return {
      ruleId: item.ruleId,
      ruleName: item.ruleName,
      count: item.count,
      cumulativePct: pct,
    }
  })

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const categories = paretoData.map(d => d.ruleId)
    const counts = paretoData.map(d => d.count)
    const pcts = paretoData.map(d => d.cumulativePct)

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const barParam = params.find((p: any) => p.seriesType === 'bar')
          if (!barParam) return ''
          const idx = barParam.dataIndex
          const item = paretoData[idx]
          return `<strong>Rule:</strong> ${item.ruleId} - ${item.ruleName}<br/><strong>Count:</strong> ${item.count}<br/><strong>Cumulative:</strong> ${item.cumulativePct}%`
        },
      },
      grid: {
        top: '15%',
        bottom: '20%',
        left: '10%',
        right: '10%',
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLabel: { interval: 0, rotate: 25, fontSize: 10 },
      },
      yAxis: [
        {
          type: 'value',
          name: 'Count',
          position: 'left',
          axisLine: { show: true },
        },
        {
          type: 'value',
          name: 'Cumulative %',
          min: 0,
          max: 100,
          position: 'right',
          axisLabel: { formatter: '{value}%' },
          axisLine: { show: true },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: 'Exception Count',
          type: 'bar',
          data: counts,
          itemStyle: { color: '#0284c7' },
        },
        {
          name: 'Cumulative %',
          type: 'line',
          yAxisIndex: 1,
          data: pcts,
          itemStyle: { color: '#d97706' },
          lineStyle: { width: 3 },
          symbol: 'circle',
          symbolSize: 6,
        },
      ],
    }

    chartInstance.current.setOption(option, true)

    chartInstance.current.off('click')
    chartInstance.current.on('click', (params: any) => {
      if (params.dataIndex !== undefined && onBarClick) {
        const item = paretoData[params.dataIndex]
        onBarClick(item.ruleId)
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [paretoData, showTable, isEmpty, onBarClick])

  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900">CHT-007: Exception Pareto (by Rule)</h3>
          <p className="text-xs text-slate-500">Frequency distribution and cumulative percentage of exceptions raised by rule.</p>
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
          <h4 className="text-sm font-bold text-slate-700">No exceptions raised in this period</h4>
          <p className="text-xs text-slate-500 mt-1 mb-4">All evaluation rules passed cleanly without raising findings.</p>
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
                <th className="py-2 px-3 border-b">Rule ID</th>
                <th className="py-2 px-3 border-b">Rule Description</th>
                <th className="py-2 px-3 border-b text-right">Count</th>
                <th className="py-2 px-3 border-b text-right">Cumulative %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {paretoData.map((it, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono font-bold text-sky-700">{it.ruleId}</td>
                  <td className="py-2 px-3 text-slate-800">{it.ruleName}</td>
                  <td className="py-2 px-3 text-right font-mono font-semibold text-slate-900">{it.count}</td>
                  <td className="py-2 px-3 text-right font-mono font-semibold text-amber-700">{it.cumulativePct}%</td>
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

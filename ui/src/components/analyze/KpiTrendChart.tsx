/**
 * CHT-001: KPI Trend Line Chart
 *
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * | CHT-001 | KPI trend | Line (multi-series, sparkline in cards) | kpi_daily aggregate · KPI × period | SCR-001, SCR-020 | KPI definition → contributing accounts (SCR-021) | "Not enough periods yet" + "Import more data" |
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle, ArrowUpRight } from 'lucide-react'

interface KpiTrendItem {
  period: string
  kpiName: string
  value: number
}

interface KpiTrendChartProps {
  items: KpiTrendItem[]
  onDrill?: (kpiName: string) => void
  onImportMore?: () => void
}

export const KpiTrendChart: React.FC<KpiTrendChartProps> = ({
  items,
  onDrill,
  onImportMore,
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !items || items.length < 2

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const periods = Array.from(new Set(items.map(i => i.period))).sort()
    const kpiNames = Array.from(new Set(items.map(i => i.kpiName)))

    const series = kpiNames.map(kpi => ({
      name: kpi,
      type: 'line',
      data: periods.map(p => {
        const found = items.find(i => i.period === p && i.kpiName === kpi)
        return found ? found.value : 0
      }),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 3 },
    }))

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let html = `<strong>Period:</strong> ${params[0].axisValue}<br/>`
          params.forEach((p: any) => {
            html += `<span style="color:${p.color}">■</span> ${p.seriesName}: <strong>${Number(p.value).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong><br/>`
          })
          return html
        },
      },
      legend: {
        data: kpiNames,
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
      series: series as any,
    }

    chartInstance.current.setOption(option, true)

    chartInstance.current.off('click')
    chartInstance.current.on('click', (params: any) => {
      if (params.seriesName && onDrill) {
        onDrill(params.seriesName)
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [items, showTable, isEmpty, onDrill])

  return (
    <div className="bg-white rounded-xl shadow border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900">CHT-001: KPI Trend Line</h3>
          <p className="text-xs text-slate-500">Multi-series KPI trend across periods with contributing account drill-down.</p>
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
          <h4 className="text-sm font-bold text-slate-700">Not enough periods yet</h4>
          <p className="text-xs text-slate-500 mt-1 mb-4">Please import additional historical period data to render KPI trends.</p>
          {onImportMore && (
            <button
              onClick={onImportMore}
              className="inline-flex items-center space-x-1 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-semibold shadow transition"
            >
              <ArrowUpRight size={14} />
              <span>Import More Data</span>
            </button>
          )}
        </div>
      ) : showTable ? (
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold sticky top-0">
              <tr>
                <th className="py-2 px-3 border-b">Period</th>
                <th className="py-2 px-3 border-b">KPI Name</th>
                <th className="py-2 px-3 border-b text-right">Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((it, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono font-semibold text-slate-900">{it.period}</td>
                  <td className="py-2 px-3 text-slate-700">{it.kpiName}</td>
                  <td className="py-2 px-3 text-right font-mono font-semibold text-sky-700">
                    {it.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div ref={chartRef} style={{ width: '100%', height: '340px' }} />
      )}
    </div>
  )
}

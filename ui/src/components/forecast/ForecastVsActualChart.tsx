/**
 * CHT-006: Forecast vs Actual Chart
 *
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * | CHT-006 | Forecast vs actual | Line + points | forecast_accuracy · period × scenario | SCR-028, SCR-019 | Point → forecast line detail (SCR-027) | "No locked forecast version yet" + "Generate" |
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle, Sparkles } from 'lucide-react'

interface ForecastActualItem {
  period: string
  actual: number
  forecast: number
}

interface ForecastVsActualChartProps {
  items: ForecastActualItem[]
  hasLockedForecast?: boolean
  onPointClick?: (period: string) => void
  onGenerateForecast?: () => void
}

export const ForecastVsActualChart: React.FC<ForecastVsActualChartProps> = ({
  items,
  hasLockedForecast = true,
  onPointClick,
  onGenerateForecast,
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !hasLockedForecast || !items || items.length === 0

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const periods = items.map(i => i.period)
    const actuals = items.map(i => i.actual)
    const forecasts = items.map(i => i.forecast)

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
        data: ['Actual', 'Locked Forecast'],
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
          name: 'Locked Forecast',
          type: 'line',
          data: forecasts,
          itemStyle: { color: '#8b5cf6' },
          lineStyle: { width: 2, type: 'dashed' },
          symbol: 'diamond',
          symbolSize: 6,
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
          <h3 className="text-base font-bold text-slate-900">CHT-006: Forecast vs Actual</h3>
          <p className="text-xs text-slate-500">Comparative accuracy line chart between actuals and locked forecast versions.</p>
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
          <h4 className="text-sm font-bold text-slate-700">No locked forecast version yet</h4>
          <p className="text-xs text-slate-500 mt-1 mb-4">Generate and lock a forecast scenario to enable forecast vs actual accuracy comparison.</p>
          {onGenerateForecast && (
            <button
              onClick={onGenerateForecast}
              className="inline-flex items-center space-x-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs font-semibold shadow transition"
            >
              <Sparkles size={14} />
              <span>Generate Forecast</span>
            </button>
          )}
        </div>
      ) : showTable ? (
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-100 text-slate-700 font-semibold sticky top-0">
              <tr>
                <th className="py-2 px-3 border-b">Period</th>
                <th className="py-2 px-3 border-b text-right">Actual (₹)</th>
                <th className="py-2 px-3 border-b text-right">Locked Forecast (₹)</th>
                <th className="py-2 px-3 border-b text-right">Variance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((it, idx) => {
                const varAmt = it.actual - it.forecast
                return (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2 px-3 font-mono font-semibold text-slate-900">{it.period}</td>
                    <td className="py-2 px-3 text-right font-mono text-sky-700">₹{it.actual.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="py-2 px-3 text-right font-mono text-purple-700">₹{it.forecast.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className={`py-2 px-3 text-right font-mono font-semibold ${varAmt < 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                      ₹{varAmt.toLocaleString(undefined, { minimumFractionDigits: 2 })}
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

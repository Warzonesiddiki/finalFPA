/**
 * CHT-011: Forecast Accuracy Trend Chart
 * 
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * - ID: CHT-011
 * - Name: Forecast accuracy trend
 * - Type: Line (error % by period) + zero line
 * - Data source: `forecast_accuracy` · period
 * - Screen: SCR-028
 * - Drill target: Point → accuracy rows for that period
 * - Empty state: "No closed periods with a locked forecast yet"
 * - Accessibility baseline: Tooltip exact values + table view toggle
 * - Centralized CF formatting: Never color-only (explicit percentage error values).
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle } from 'lucide-react'

interface AccuracyItem {
  period: string
  errorPct: number
}

interface ForecastAccuracyTrendChartProps {
  items: AccuracyItem[]
  onPointClick?: (period: string) => void
}

export const ForecastAccuracyTrendChart: React.FC<ForecastAccuracyTrendChartProps> = ({ items, onPointClick }) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !items || items.length === 0

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const periods = items.map(i => i.period)
    const errors = items.map(i => i.errorPct)

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const item = items[params[0].dataIndex]
          return `<strong>${item.period}</strong><br/>Forecast Error: ${item.errorPct}%`
        },
      },
      grid: { top: 20, right: 20, bottom: 30, left: 50, containLabel: true },
      xAxis: { type: 'category', data: periods, axisLabel: { fontSize: 11 } },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: (val: number) => `${val}%` },
      },
      series: [
        {
          type: 'line',
          data: errors,
          smooth: true,
          itemStyle: { color: '#0284c7' },
          lineStyle: { width: 3 },
          markLine: {
            data: [{ yAxis: 0, lineStyle: { color: '#94a3b8', type: 'dashed' } }],
            silent: true,
          },
        },
      ],
    }

    chartInstance.current.setOption(option)

    chartInstance.current.off('click')
    chartInstance.current.on('click', params => {
      if (onPointClick && params.name) {
        onPointClick(params.name)
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [items, showTable, isEmpty, onPointClick])

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h4 style={{ margin: '0 0 2px', fontSize: '15px', color: '#0f172a' }}>CHT-011: Forecast Accuracy Trend</h4>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Percentage variance error between locked forecast and actuals</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setShowTable(!showTable)}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '12px', fontWeight: 600, cursor: 'pointer', color: '#334155' }}
          >
            {showTable ? <BarChart3 size={14} /> : <Table size={14} />}
            {showTable ? 'Chart View' : 'Table View'}
          </button>
        </div>
      </div>

      {isEmpty ? (
        <div style={{ padding: '40px 20px', textAlign: 'center', color: '#64748b', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={28} color="#94a3b8" />
          <div style={{ fontWeight: 600, fontSize: '14px' }}>No closed periods with a locked forecast yet</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>Generate and lock forecast versions for closed periods to view accuracy trends.</div>
        </div>
      ) : showTable ? (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
              <th style={{ padding: '10px' }}>Period</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Forecast Error (%)</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '10px', fontWeight: 600, color: '#1e293b' }}>{item.period}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600, color: item.errorPct > 10 ? '#dc2626' : '#16a34a' }}>
                  {item.errorPct}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div ref={chartRef} style={{ width: '100%', height: '260px' }} />
      )}
    </div>
  )
}

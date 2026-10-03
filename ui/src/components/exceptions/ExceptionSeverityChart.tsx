/**
 * CHT-008: Exception Severity Mix Chart
 * 
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * - ID: CHT-008
 * - Name: Exception severity mix
 * - Type: Stacked bar by period
 * - Data source: `exception_stats` · severity × period
 * - Screen: SCR-026
 * - Drill target: Segment → filtered register (SCR-023)
 * - Empty state: "No exceptions raised in this period"
 * - Accessibility baseline: Tooltip exact values + table view toggle
 * - Centralized CF formatting: Never color-only (explicit counts and severity labels).
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle } from 'lucide-react'

interface SeverityPeriodItem {
  period: string
  critical: number
  warning: number
  info: number
}

interface ExceptionSeverityChartProps {
  items: SeverityPeriodItem[]
  onSegmentClick?: (period: string, severity: string) => void
}

export const ExceptionSeverityChart: React.FC<ExceptionSeverityChartProps> = ({ items, onSegmentClick }) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !items || items.length === 0 || items.every(i => i.critical === 0 && i.warning === 0 && i.info === 0)

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const periods = items.map(i => i.period)
    const criticals = items.map(i => i.critical)
    const warnings = items.map(i => i.warning)
    const infos = items.map(i => i.info)

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
      },
      legend: { data: ['Critical', 'Warning', 'Info'], bottom: 0, textStyle: { fontSize: 11 } },
      grid: { top: 20, right: 20, bottom: 40, left: 40, containLabel: true },
      xAxis: { type: 'category', data: periods, axisLabel: { fontSize: 11 } },
      yAxis: { type: 'value' },
      series: [
        { name: 'Critical', type: 'bar', stack: 'total', data: criticals, itemStyle: { color: '#dc2626' } },
        { name: 'Warning', type: 'bar', stack: 'total', data: warnings, itemStyle: { color: '#d97706' } },
        { name: 'Info', type: 'bar', stack: 'total', data: infos, itemStyle: { color: '#0284c7' } },
      ],
    }

    chartInstance.current.setOption(option)

    chartInstance.current.off('click')
    chartInstance.current.on('click', params => {
      if (onSegmentClick && params.name && params.seriesName) {
        onSegmentClick(params.name, params.seriesName.toLowerCase())
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [items, showTable, isEmpty, onSegmentClick])

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h4 style={{ margin: '0 0 2px', fontSize: '15px', color: '#0f172a' }}>CHT-008: Exception Severity Mix</h4>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Distribution of exception severities by accounting period</span>
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
          <div style={{ fontWeight: 600, fontSize: '14px' }}>No exceptions raised in this period</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>Run exception rules to populate severity distribution.</div>
        </div>
      ) : showTable ? (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
              <th style={{ padding: '10px' }}>Period</th>
              <th style={{ padding: '10px', textAlign: 'right', color: '#dc2626' }}>Critical</th>
              <th style={{ padding: '10px', textAlign: 'right', color: '#d97706' }}>Warning</th>
              <th style={{ padding: '10px', textAlign: 'right', color: '#0284c7' }}>Info</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '10px', fontWeight: 600, color: '#1e293b' }}>{item.period}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontFamily: 'monospace' }}>{item.critical}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontFamily: 'monospace' }}>{item.warning}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontFamily: 'monospace' }}>{item.info}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>{item.critical + item.warning + item.info}</td>
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

/**
 * CHT-010: Exception Aging Distribution Chart
 * 
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * - ID: CHT-010
 * - Name: Exception aging distribution
 * - Type: Bars by bucket (`0–7`, `8–30`, `31+`)
 * - Data source: `exception_stats` · bucket × severity
 * - Screen: SCR-023, SCR-026
 * - Drill target: Bar → filtered register
 * - Empty state: "No open exceptions"
 * - Accessibility baseline: Tooltip exact values + table view toggle
 * - Centralized CF formatting: Never color-only (explicit counts and aging bucket labels).
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle } from 'lucide-react'

interface AgingBucketItem {
  bucket: string
  count: number
}

interface ExceptionAgingChartProps {
  items: AgingBucketItem[]
  onBucketClick?: (bucket: string) => void
}

export const ExceptionAgingChart: React.FC<ExceptionAgingChartProps> = ({ items, onBucketClick }) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !items || items.length === 0 || items.every(i => i.count === 0)

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const buckets = items.map(i => i.bucket)
    const counts = items.map(i => i.count)

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
      },
      grid: { top: 20, right: 20, bottom: 30, left: 40, containLabel: true },
      xAxis: { type: 'category', data: buckets, axisLabel: { fontSize: 11 } },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'bar',
          data: counts,
          itemStyle: { color: '#0284c7' },
          barWidth: '50%',
        },
      ],
    }

    chartInstance.current.setOption(option)

    chartInstance.current.off('click')
    chartInstance.current.on('click', params => {
      if (onBucketClick && params.name) {
        onBucketClick(params.name)
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [items, showTable, isEmpty, onBucketClick])

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h4 style={{ margin: '0 0 2px', fontSize: '15px', color: '#0f172a' }}>CHT-010: Exception Aging Distribution</h4>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Open exceptions grouped by aging buckets (0–7, 8–30, 31+ days)</span>
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
          <div style={{ fontWeight: 600, fontSize: '14px' }}>No open exceptions</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>All raised exceptions have been resolved or closed.</div>
        </div>
      ) : showTable ? (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
              <th style={{ padding: '10px' }}>Aging Bucket</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Open Count</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '10px', fontWeight: 600, color: '#1e293b' }}>{item.bucket} Days</td>
                <td style={{ padding: '10px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600 }}>{item.count}</td>
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

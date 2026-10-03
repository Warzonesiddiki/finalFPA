/**
 * CHT-002: BvA Bridge / Waterfall Chart
 * 
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * - ID: CHT-002
 * - Name: BvA bridge
 * - Type: Waterfall
 * - Data source: `bva_drivers` · driver × period
 * - Screen: SCR-016
 * - Drill target: Bar → driver rows (SCR-021)
 * - Empty state: "No variances to bridge in this window"
 * - Accessibility baseline: Tooltip exact values + table view toggle
 * - Centralized CF formatting: Never color-only (explicit amounts with ▲/▼ indicators).
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle } from 'lucide-react'

interface BridgeItem {
  name: string
  value: number
  isTotal?: boolean
}

interface BvaBridgeChartProps {
  items: BridgeItem[]
  onBarClick?: (name: string) => void
}

export const BvaBridgeChart: React.FC<BvaBridgeChartProps> = ({ items, onBarClick }) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isEmpty = !items || items.length === 0

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    // Compute waterfall baselines (invisible stack base + visible bar)
    let cumulative = 0
    const base: number[] = []
    const positive: number[] = []
    const negative: number[] = []

    items.forEach((item, idx) => {
      if (item.isTotal || idx === 0) {
        base.push(0)
        positive.push(item.value)
        negative.push(0)
        cumulative = item.value
      } else if (item.value >= 0) {
        base.push(cumulative)
        positive.push(item.value)
        negative.push(0)
        cumulative += item.value
      } else {
        cumulative += item.value
        base.push(cumulative)
        positive.push(0)
        negative.push(Math.abs(item.value))
      }
    })

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const idx = params[0].dataIndex
          const item = items[idx]
          const sign = item.value >= 0 ? '+' : ''
          return `<strong>${item.name}</strong><br/>Variance: ${sign}$${item.value.toLocaleString()}`
        },
      },
      grid: { top: 20, right: 20, bottom: 40, left: 60, containLabel: true },
      xAxis: {
        type: 'category',
        data: items.map(i => i.name),
        axisLabel: { interval: 0, rotate: 15, fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: (val: number) => `$${(val / 1000).toFixed(0)}k` },
      },
      series: [
        {
          name: 'Placeholder',
          type: 'bar',
          stack: 'all',
          itemStyle: { borderColor: 'transparent', color: 'transparent' },
          emphasis: { itemStyle: { borderColor: 'transparent', color: 'transparent' } },
          data: base,
        },
        {
          name: 'Favourable / Increase',
          type: 'bar',
          stack: 'all',
          itemStyle: { color: '#16a34a' },
          data: positive,
        },
        {
          name: 'Adverse / Decrease',
          type: 'bar',
          stack: 'all',
          itemStyle: { color: '#dc2626' },
          data: negative,
        },
      ],
    }

    chartInstance.current.setOption(option)

    chartInstance.current.off('click')
    chartInstance.current.on('click', params => {
      if (onBarClick && params.name) {
        onBarClick(params.name)
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [items, showTable, isEmpty, onBarClick])

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h4 style={{ margin: '0 0 2px', fontSize: '15px', color: '#0f172a' }}>CHT-002: BvA Bridge &amp; Driver Waterfall</h4>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Walks variance drivers from baseline budget to actuals</span>
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
        <div style={{ padding: '50px 20px', textAlign: 'center', color: '#64748b', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={28} color="#94a3b8" />
          <div style={{ fontWeight: 600, fontSize: '14px' }}>No variances to bridge in this window</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>Import actuals and budgets to generate variance waterfall bridge.</div>
        </div>
      ) : showTable ? (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
              <th style={{ padding: '10px' }}>Driver / Component</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Variance Impact</th>
              <th style={{ padding: '10px' }}>Direction</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '10px', fontWeight: 600, color: '#1e293b' }}>{item.name}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600, color: item.value >= 0 ? '#16a34a' : '#dc2626' }}>
                  {item.value >= 0 ? '+' : ''}${item.value.toLocaleString()}
                </td>
                <td style={{ padding: '10px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: item.value >= 0 ? '#16a34a' : '#dc2626' }}>
                    {item.value >= 0 ? '▲ FAVOURABLE' : '▼ ADVERSE'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div ref={chartRef} style={{ width: '100%', height: '320px' }} />
      )}
    </div>
  )
}

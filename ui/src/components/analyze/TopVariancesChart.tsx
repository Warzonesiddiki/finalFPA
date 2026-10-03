/**
 * CHT-003 & CHT-004: Top Adverse and Top Favourable Variance Charts
 * 
 * Quoted from docs/08_UI_UX_SPEC.md §13 (Chart Inventory):
 * - ID: CHT-003 / CHT-004
 * - Name: Top adverse variances / Top favourable variances
 * - Type: Horizontal bars
 * - Data source: `bva_topn` · account/CC × period
 * - Screen: SCR-018
 * - Drill target: Bar → drill list for that key (SCR-021)
 * - Empty state: "No adverse variances" / "No favourable variances"
 * - Accessibility baseline: Tooltip exact values + table view toggle
 * - Centralized CF formatting: Never color-only (explicit values and explicit indicators).
 */

import React, { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { BarChart3, Table, AlertCircle } from 'lucide-react'

interface VarianceItem {
  key: string
  label: string
  amount: number
}

interface TopVariancesChartProps {
  type: 'adverse' | 'favourable'
  items: VarianceItem[]
  onBarClick?: (key: string) => void
}

export const TopVariancesChart: React.FC<TopVariancesChartProps> = ({ type, items, onBarClick }) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [showTable, setShowTable] = useState(false)

  const isAdverse = type === 'adverse'
  const title = isAdverse ? 'CHT-003: Top Adverse Variances' : 'CHT-004: Top Favourable Variances'
  const emptyMsg = isAdverse ? 'No adverse variances' : 'No favourable variances'
  const barColor = isAdverse ? '#dc2626' : '#16a34a'

  const filteredItems = [...items]
    .filter(i => (isAdverse ? i.amount < 0 : i.amount > 0))
    .sort((a, b) => (isAdverse ? a.amount - b.amount : b.amount - a.amount))
    .slice(0, 5)

  const isEmpty = filteredItems.length === 0

  useEffect(() => {
    if (isEmpty || showTable || !chartRef.current) return

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current)
    }

    const categories = filteredItems.map(i => i.label).reverse()
    const values = filteredItems.map(i => Math.abs(i.amount)).reverse()

    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const item = filteredItems[filteredItems.length - 1 - params[0].dataIndex]
          return `<strong>${item.label}</strong><br/>Variance: $${item.amount.toLocaleString()}`
        },
      },
      grid: { top: 10, right: 20, bottom: 20, left: 100, containLabel: true },
      xAxis: {
        type: 'value',
        axisLabel: { formatter: (val: number) => `$${(val / 1000).toFixed(0)}k` },
      },
      yAxis: {
        type: 'category',
        data: categories,
        axisLabel: { fontSize: 11 },
      },
      series: [
        {
          type: 'bar',
          data: values,
          itemStyle: { color: barColor },
          barWidth: '60%',
        },
      ],
    }

    chartInstance.current.setOption(option)

    chartInstance.current.off('click')
    chartInstance.current.on('click', params => {
      if (onBarClick) {
        const item = filteredItems[filteredItems.length - 1 - params.dataIndex]
        if (item) onBarClick(item.key)
      }
    })

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [filteredItems, showTable, isEmpty, barColor, onBarClick])

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h4 style={{ margin: '0 0 2px', fontSize: '15px', color: '#0f172a' }}>{title}</h4>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Top 5 variance drivers by magnitude</span>
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
          <div style={{ fontWeight: 600, fontSize: '14px' }}>{emptyMsg}</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>All accounts are within budget tolerance.</div>
        </div>
      ) : showTable ? (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#64748b' }}>
              <th style={{ padding: '10px' }}>Account / Cost Centre</th>
              <th style={{ padding: '10px', textAlign: 'right' }}>Variance Amount</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '10px', fontWeight: 600, color: '#1e293b' }}>{item.label}</td>
                <td style={{ padding: '10px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 600, color: barColor }}>
                  ${item.amount.toLocaleString()}
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

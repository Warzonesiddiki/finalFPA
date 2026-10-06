/**
 * Stale-Derived Data Banner Component (Addon 2 B.7 / docs 08/09)
 *
 * Quoted from Addon 2 B.7 / docs 08 & 09 (Recompute & Invalidation / Staleness):
 * "When mappings, thresholds, or master data are modified (e.g. via Settings or Master Data screens), all downstream derived results (Budget vs. Actual analysis, exception rule findings, and scenario forecasts) shall be automatically marked as STALE in the application state and database.
 * The user shall never be shown silently outdated derived numbers. A prominent 'Re-run required — configuration changed' banner shall be displayed across the Analyze, Exceptions, and Forecast screens.
 * An explicit 'Re-run Now' action button on the banner shall trigger re-computation of analytics, rule evaluation, and forecasts, clearing the staleness flag upon successful completion."
 */

import { useState, useEffect } from 'react'

interface StaleBannerProps {
  sessionToken: string
  onRerunComplete?: () => void
}

export function StaleBanner({ sessionToken, onRerunComplete }: StaleBannerProps) {
  const [isStale, setIsStale] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [staleReason, setStaleReason] = useState<string | null>(null)

  const checkStaleness = () => {
    fetch('/api/v1/staleness', {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setIsStale(data.data?.isStale || false)
          setStaleReason(data.data?.reason || null)
        }
      })
      .catch(() => {})
  }

  useEffect(() => {
    checkStaleness()
    const interval = setInterval(checkStaleness, 5000)
    return () => clearInterval(interval)
  }, [sessionToken])

  const handleRerun = () => {
    setLoading(true)
    setMessage(null)
    fetch('/api/v1/staleness/rerun', {
      method: 'POST',
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        setLoading(false)
        if (data.status === 'ok') {
          setIsStale(false)
          setMessage(null)
          if (onRerunComplete) onRerunComplete()
        } else {
          setMessage('Re-run failed: ' + (data.detail || data.message || 'Unknown error'))
        }
      })
      .catch(err => {
        setLoading(false)
        setMessage('Network error during re-run: ' + String(err))
      })
  }

  if (!isStale && !message) return null

  return (
    <div style={{ backgroundColor: '#fef3c7', border: '1px solid #f59e0b', borderRadius: '6px', padding: '12px 16px', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ fontSize: '13px', color: '#92400e' }}>
        <strong>⚠ Re-run Required — Configuration Changed:</strong>{' '}
        {message || staleReason || 'Mappings, thresholds, or master data have been modified. Derived analytics, exceptions, and forecasts are stale. You are not viewing live numbers.'}
      </div>
      {isStale && (
        <button
          disabled={loading}
          onClick={handleRerun}
          style={{ backgroundColor: '#d97706', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '4px', fontSize: '12px', fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap', marginLeft: '16px' }}
        >
          {loading ? 'Re-running...' : 'Re-run Now'}
        </button>
      )}
    </div>
  )
}

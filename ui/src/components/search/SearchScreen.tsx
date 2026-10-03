/**
 * Global Search Screen (SCR-022)
 *
 * Functional Requirements quoted from docs/02_FUNCTIONAL_SPEC.md & docs/08_UI_UX_SPEC.md:
 * - FR-BVA-012 · P1 · Phase 2 — Search:
 *   "One search box finds vouchers, vendors, descriptions and accounts across loaded periods;
 *   results are grouped by type with counts, show the source batch per row, and land in a
 *   pre-filtered transaction list. Performance target is owned by doc 14 (<200ms)."
 */

import { useState, useEffect, useRef } from 'react'

interface SearchResultItem {
  actualId: number
  importBatchId: number
  sourceFileName: string
  sourceRowRef: string
  postingDate: string
  voucherNo: string
  lineNo: number
  invoiceNo?: string
  description: string
  debit: string
  credit: string
  netAmount: string
  companyCode: string
  accountCode: string
  accountName: string
  statementLine: string
  costCenterCode: string
  periodCode: string
}

export function SearchScreen({ sessionToken }: { sessionToken: string }) {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [items, setItems] = useState<SearchResultItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [elapsedMs, setElapsedMs] = useState<number | null>(null)
  const [selectedItem, setSelectedItem] = useState<SearchResultItem | null>(null)

  const inputRef = useRef<HTMLInputElement>(null)

  // Debounce query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
      setPage(1)
    }, 250)
    return () => clearTimeout(timer)
  }, [query])

  // Fetch search results
  useEffect(() => {
    const startTime = performance.now()
    setLoading(true)
    fetch(`/api/v1/search?q=${encodeURIComponent(debouncedQuery)}&page=${page}&page_size=${pageSize}`, {
      headers: { 'X-Session-Token': sessionToken },
    })
      .then(res => res.json())
      .then(data => {
        const endTime = performance.now()
        setElapsedMs(Math.round(endTime - startTime))
        setLoading(false)
        if (data.status === 'ok' && data.data) {
          setItems(data.data.items || [])
          setTotal(data.data.total || 0)
          setHasMore(data.data.hasMore || false)
        }
      })
      .catch(() => {
        setLoading(false)
        setElapsedMs(null)
      })
  }, [debouncedQuery, page, pageSize, sessionToken])

  // Group items by category (Voucher, Vendor/Invoice, Description, Account)
  const voucherCount = items.filter(i => i.voucherNo?.toLowerCase().includes(debouncedQuery.toLowerCase())).length
  const vendorCount = items.filter(i => i.invoiceNo?.toLowerCase().includes(debouncedQuery.toLowerCase())).length
  const accountCount = items.filter(i => i.accountCode?.toLowerCase().includes(debouncedQuery.toLowerCase()) || i.accountName?.toLowerCase().includes(debouncedQuery.toLowerCase())).length

  return (
    <div style={{ padding: '24px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', minHeight: '600px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: '0 0 6px', fontSize: '18px', color: '#1e293b' }}>
            🔍 Global Search across Loaded Periods (SCR-022 / FR-BVA-012)
          </h2>
          <p style={{ margin: 0, color: '#64748b', fontSize: '13px' }}>
            Instant server-side search across vouchers, vendors/invoice numbers, descriptions, and accounts. Performance target: &lt;200ms.
          </p>
        </div>
        {elapsedMs !== null && (
          <div style={{ backgroundColor: elapsedMs < 200 ? '#dcfce7' : '#fef9c3', color: elapsedMs < 200 ? '#166534' : '#854d0e', padding: '6px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: 600, border: '1px solid ' + (elapsedMs < 200 ? '#16a34a' : '#ca8a04') }}>
            ⚡ Response Time: {elapsedMs}ms {elapsedMs < 200 ? '(Meets Doc 14 Target)' : ''}
          </div>
        )}
      </div>

      {/* Search Input Box */}
      <div style={{ marginBottom: '20px', position: 'relative' }}>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search vouchers (e.g. V-001), vendors/invoices, descriptions, accounts..."
          style={{ width: '100%', padding: '12px 16px', fontSize: '15px', borderRadius: '8px', border: '1px solid #cbd5e1', outline: 'none', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}
        />
        {query && (
          <button
            onClick={() => setQuery('')}
            style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', fontSize: '16px', fontWeight: 'bold' }}
          >
            ×
          </button>
        )}
      </div>

      {/* Summary Chips / Counts */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', fontSize: '13px', color: '#475569' }}>
        <div style={{ backgroundColor: '#f1f5f9', padding: '6px 12px', borderRadius: '6px' }}>
          Total Matches: <b>{total}</b>
        </div>
        <div style={{ backgroundColor: '#f1f5f9', padding: '6px 12px', borderRadius: '6px' }}>
          Voucher Matches: <b>{voucherCount}</b>
        </div>
        <div style={{ backgroundColor: '#f1f5f9', padding: '6px 12px', borderRadius: '6px' }}>
          Vendor/Invoice Matches: <b>{vendorCount}</b>
        </div>
        <div style={{ backgroundColor: '#f1f5f9', padding: '6px 12px', borderRadius: '6px' }}>
          Account Matches: <b>{accountCount}</b>
        </div>
      </div>

      {/* Results Table */}
      <div style={{ border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
              <th style={{ padding: '10px 12px' }}>Voucher No</th>
              <th style={{ padding: '10px 12px' }}>Posting Date / Period</th>
              <th style={{ padding: '10px 12px' }}>Company / Account</th>
              <th style={{ padding: '10px 12px' }}>Description &amp; Invoice</th>
              <th style={{ padding: '10px 12px' }}>Source Batch</th>
              <th style={{ padding: '10px 12px', textAlign: 'right' }}>Net Amount (INR)</th>
              <th style={{ padding: '10px 12px', textAlign: 'center' }}>Drill-Through</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>
                  Searching across loaded periods...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>
                  {debouncedQuery ? `No matching transactions found for "${debouncedQuery}".` : 'Enter a search term to find transactions across loaded periods.'}
                </td>
              </tr>
            ) : (
              items.map(item => (
                <tr key={item.actualId} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 600, color: '#0284c7' }}>{item.voucherNo}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <div>{item.postingDate}</div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>{item.periodCode}</div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ fontWeight: 500 }}>{item.accountCode} - {item.accountName}</div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>{item.companyCode} | {item.costCenterCode}</div>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div>{item.description}</div>
                    {item.invoiceNo && <div style={{ fontSize: '11px', color: '#64748b' }}>Inv: {item.invoiceNo}</div>}
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: '11px', color: '#475569', fontFamily: 'monospace' }}>
                    {item.sourceFileName}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 600, color: Number(item.netAmount) < 0 ? '#dc2626' : '#0f172a' }}>
                    {Number(item.netAmount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                    <button
                      onClick={() => setSelectedItem(item)}
                      style={{ backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', cursor: 'pointer', fontWeight: 500, color: '#0284c7' }}
                    >
                      🔗 Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
        <div style={{ fontSize: '12px', color: '#64748b' }}>
          Showing page {page} ({items.length} items of {total} total)
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            style={{ padding: '6px 12px', backgroundColor: page <= 1 ? '#f1f5f9' : '#fff', border: '1px solid #cbd5e1', borderRadius: '4px', cursor: page <= 1 ? 'not-allowed' : 'pointer', fontSize: '12px' }}
          >
            Previous
          </button>
          <button
            disabled={!hasMore}
            onClick={() => setPage(p => p + 1)}
            style={{ padding: '6px 12px', backgroundColor: !hasMore ? '#f1f5f9' : '#fff', border: '1px solid #cbd5e1', borderRadius: '4px', cursor: !hasMore ? 'not-allowed' : 'pointer', fontSize: '12px' }}
          >
            Next
          </button>
        </div>
      </div>

      {/* Drill-through / Inspect Modal */}
      {selectedItem && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: '#fff', borderRadius: '8px', width: '600px', maxWidth: '90%', padding: '24px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '16px', color: '#1e293b' }}>
              Transaction Drill-Through: {selectedItem.voucherNo}
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px', marginBottom: '20px' }}>
              <div><b>Actual ID:</b> {selectedItem.actualId}</div>
              <div><b>Posting Date:</b> {selectedItem.postingDate}</div>
              <div><b>Period:</b> {selectedItem.periodCode}</div>
              <div><b>Company:</b> {selectedItem.companyCode}</div>
              <div><b>Account:</b> {selectedItem.accountCode} - {selectedItem.accountName}</div>
              <div><b>Cost Center:</b> {selectedItem.costCenterCode}</div>
              <div><b>Invoice / Ref:</b> {selectedItem.invoiceNo || 'N/A'}</div>
              <div><b>Statement Line:</b> {selectedItem.statementLine}</div>
              <div style={{ gridColumn: 'span 2' }}><b>Description:</b> {selectedItem.description}</div>
              <div><b>Debit:</b> INR {Number(selectedItem.debit).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div><b>Credit:</b> INR {Number(selectedItem.credit).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div style={{ gridColumn: 'span 2', fontWeight: 'bold' }}>Net Amount: INR {Number(selectedItem.netAmount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              <div style={{ gridColumn: 'span 2', fontSize: '11px', color: '#64748b' }}>
                <b>Source File:</b> {selectedItem.sourceFileName} (Row Ref: {selectedItem.sourceRowRef})
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSelectedItem(null)}
                style={{ backgroundColor: '#0284c7', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', fontWeight: 600 }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

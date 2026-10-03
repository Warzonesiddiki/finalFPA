import React, { useState } from 'react'
import { FileSpreadsheet, Check, ArrowLeft, ArrowRight, Eye, Info } from 'lucide-react'
import { FileItem } from './types'

interface SheetHeaderStepProps {
  file: FileItem
  onUpdateFile: (updated: Partial<FileItem>) => void
  onBack: () => void
  onNext: () => void
}

// Sample raw grid data representing realistic preview rows for the file
const SAMPLE_GRID_PREVIEWS: Record<string, { banner?: string; rows: string[][] }> = {
  'procurement_bank': {
    banner: '# SAMPLE DATA — NOT FOR PRODUCTION USE',
    rows: [
      ['BankAccountId', 'ValueDate', 'DocNumber', 'EntityId', 'AccountCode', 'Narration', 'Withdrawal', 'Deposit', 'RunningBalance'],
      ['HDFC-0019283', '05/08/2026', 'BNK-10001', 'IN01', '1020', 'Settlement batch 1', '36519.00', '0.00', '14963481.00'],
      ['HDFC-0019283', '01/06/2026', 'BNK-10002', 'IN01', '1020', 'Settlement batch 2', '46011.00', '0.00', '14917470.00'],
      ['HDFC-0019283', '20/04/2026', 'BNK-10003', 'IN01', '1020', 'Settlement batch 3', '24866.00', '0.00', '14892604.00'],
      ['HDFC-0019283', '14/06/2026', 'BNK-10004', 'IN01', '1020', 'Settlement batch 4', '27885.00', '0.00', '14864719.00'],
      ['HDFC-0019283', '27/04/2026', 'BNK-10005', 'IN01', '1020', 'Settlement batch 5', '40495.00', '0.00', '14824224.00'],
    ],
  },
  'd365_gl': {
    rows: [
      ['Company', 'Ledger account', 'Posting date', 'Fiscal period', 'Voucher', 'Line', 'Debit', 'Credit', 'Department', 'Notes'],
      ['IN01', '5200-10', '14-09-2026', 'FY26-P09', 'VCH-2026-0912-004', '1', '45000.00', '0.00', 'Dept=100|CC=200', 'Repairs - plant'],
      ['IN01', '5200-10', '14-09-2026', 'FY26-P09', 'VCH-2026-0912-004', '2', '0.00', '45000.00', 'Dept=100|CC=200', 'Repairs - plant offset'],
      ['IN02', '4110-00', '15-09-2026', 'FY26-P09', 'VCH-2026-0915-010', '1', '12500.00', '0.00', 'Dept=200|CC=100', 'Consulting fee'],
      ['IN02', '4110-00', '15-09-2026', 'FY26-P09', 'VCH-2026-0915-010', '2', '0.00', '12500.00', 'Dept=200|CC=100', 'Consulting fee accrual'],
    ],
  },
  'budget': {
    rows: [
      ['FiscalYear', 'FiscalPeriod', 'EntityId', 'AccountCode', 'CostCenter', 'Department', 'BudgetAmount', 'Currency'],
      ['FY26', 'FY26-P09', 'IN01', '5200-10', 'CC-200', 'Operations', '380000.00', 'INR'],
      ['FY26', 'FY26-P09', 'IN01', '4110-00', 'CC-100', 'Administration', '120000.00', 'INR'],
      ['FY26', 'FY26-P09', 'IN01', '5300-00', 'CC-200', 'Operations', '540000.00', 'INR'],
      ['FY26', 'FY26-P09', 'IN02', '4000-10', 'CC-300', 'Commercial', '10000000.00', 'INR'],
    ],
  },
}

export const SheetHeaderStep: React.FC<SheetHeaderStepProps> = ({
  file,
  onUpdateFile,
  onBack,
  onNext,
}) => {
  const [selectedSheet, setSelectedSheet] = useState(file.selectedSheet || file.sheets[0] || 'Sheet1')
  const [headerRowIndex, setHeaderRowIndex] = useState(file.headerRowIndex || (file.bannerDetected ? 2 : 1))
  const [dataStartRowIndex, setDataStartRowIndex] = useState(file.dataStartRowIndex || (headerRowIndex + 1))
  const [additionalHeaderRows, setAdditionalHeaderRows] = useState(0)

  const previewConfig = SAMPLE_GRID_PREVIEWS[file.detectedSourceType] || SAMPLE_GRID_PREVIEWS['d365_gl']

  // Build simulated row preview including banner if detected
  const previewRows: { rowIndex: number; isBanner?: boolean; cells: string[] }[] = []

  if (file.bannerDetected && file.bannerText) {
    previewRows.push({
      rowIndex: 1,
      isBanner: true,
      cells: [file.bannerText],
    })
    previewConfig.rows.forEach((r, idx) => {
      previewRows.push({
        rowIndex: idx + 2,
        cells: r,
      })
    })
  } else {
    previewConfig.rows.forEach((r, idx) => {
      previewRows.push({
        rowIndex: idx + 1,
        cells: r,
      })
    })
  }

  const handleSelectHeaderRow = (rowIdx: number) => {
    setHeaderRowIndex(rowIdx)
    setDataStartRowIndex(rowIdx + 1)
    onUpdateFile({
      headerRowIndex: rowIdx,
      dataStartRowIndex: rowIdx + 1,
    })
  }

  const handleSheetChange = (sheet: string) => {
    setSelectedSheet(sheet)
    onUpdateFile({ selectedSheet: sheet })
  }

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#0284c7', fontWeight: 700 }}>
          SCR-007 &bull; Step 3 of 6
        </span>
        <h2 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>
          Sheet &amp; Header Row Selection
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
          Select the active workbook sheet and designate the table header row. Non-data title banners are skipped automatically.
        </p>
      </div>

      {/* Control Bar: Sheet Picker & Header Settings */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        {/* Sheet Picker */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ fontSize: '13px', fontWeight: 600, color: '#334155', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <FileSpreadsheet size={16} color="#0284c7" /> Active Sheet:
          </label>
          <select
            value={selectedSheet}
            onChange={e => handleSheetChange(e.target.value)}
            style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', fontWeight: 600, color: '#0f172a' }}
          >
            {file.sheets.map(s => (
              <option key={s} value={s}>
                {s} (active)
              </option>
            ))}
          </select>
          {file.sheetCount > 1 && (
            <span style={{ fontSize: '11px', color: '#64748b' }}>
              ({file.sheetCount - 1} other sheet{file.sheetCount > 2 ? 's' : ''} skipped)
            </span>
          )}
        </div>

        {/* Header Row Index Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '13px', color: '#475569' }}>Header row:</span>
            <span style={{ padding: '3px 8px', backgroundColor: '#e0f2fe', color: '#0369a1', borderRadius: '4px', fontWeight: 700, fontSize: '13px' }}>
              Row {headerRowIndex}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '13px', color: '#475569' }}>Data starts at:</span>
            <span style={{ padding: '3px 8px', backgroundColor: '#f1f5f9', color: '#334155', borderRadius: '4px', fontWeight: 700, fontSize: '13px' }}>
              Row {dataStartRowIndex}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Multi-row header:</span>
            <input
              type="number"
              min="0"
              max="3"
              value={additionalHeaderRows}
              onChange={e => setAdditionalHeaderRows(Number(e.target.value))}
              style={{ width: '45px', padding: '4px', border: '1px solid #cbd5e1', borderRadius: '4px', fontSize: '12px' }}
            />
          </div>
        </div>
      </div>

      {/* Grid Preview */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', marginBottom: '24px' }}>
        <div style={{ padding: '12px 16px', backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, color: '#334155' }}>
            <Eye size={16} color="#64748b" />
            <span>Interactive Data Grid Preview &bull; Click any row to set as Column Header</span>
          </div>
          <span style={{ fontSize: '12px', color: '#64748b' }}>
            Showing first {previewRows.length} rows &bull; Encoded as {file.detectedEncoding}
          </span>
        </div>

        <div style={{ overflowX: 'auto', maxHeight: '420px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <tbody>
              {previewRows.map(row => {
                const isSelectedHeader = row.rowIndex === headerRowIndex
                const isBannerRow = !!row.isBanner

                return (
                  <tr
                    key={row.rowIndex}
                    onClick={() => !isBannerRow && handleSelectHeaderRow(row.rowIndex)}
                    style={{
                      borderBottom: '1px solid #e2e8f0',
                      cursor: isBannerRow ? 'default' : 'pointer',
                      backgroundColor: isSelectedHeader
                        ? '#e0f2fe'
                        : isBannerRow
                        ? '#fffbeb'
                        : '#ffffff',
                      transition: 'background-color 0.1s ease',
                    }}
                  >
                    {/* Row Index Indicator Cell */}
                    <td
                      style={{
                        padding: '10px 14px',
                        width: '90px',
                        fontWeight: 600,
                        color: isSelectedHeader ? '#0369a1' : isBannerRow ? '#b45309' : '#64748b',
                        borderRight: '1px solid #e2e8f0',
                        backgroundColor: isSelectedHeader ? '#bae6fd' : isBannerRow ? '#fef3c7' : '#f8fafc',
                        textAlign: 'center',
                        userSelect: 'none',
                      }}
                    >
                      {isBannerRow ? (
                        <span style={{ fontSize: '11px', color: '#b45309', fontWeight: 700 }}>BANNER 1</span>
                      ) : isSelectedHeader ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontWeight: 700 }}>
                          <Check size={13} /> ROW {row.rowIndex}
                        </span>
                      ) : (
                        `Row ${row.rowIndex}`
                      )}
                    </td>

                    {/* Data Cells */}
                    {isBannerRow ? (
                      <td
                        colSpan={8}
                        style={{
                          padding: '10px 16px',
                          color: '#b45309',
                          fontStyle: 'italic',
                          fontFamily: 'monospace',
                        }}
                      >
                        {row.cells[0]} &bull; (Detected title/comment banner — excluded from column mapping)
                      </td>
                    ) : (
                      row.cells.map((cell, cIdx) => (
                        <td
                          key={cIdx}
                          style={{
                            padding: '10px 14px',
                            whiteSpace: 'nowrap',
                            color: isSelectedHeader ? '#0c4a6e' : '#1e293b',
                            fontWeight: isSelectedHeader ? 700 : 400,
                            fontFamily: isSelectedHeader ? 'inherit' : 'monospace',
                          }}
                        >
                          {cell}
                        </td>
                      ))
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info Notice Box */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', color: '#166534', fontSize: '13px', marginBottom: '24px' }}>
        <Info size={16} />
        <span>
          Header row configured at <strong>Row {headerRowIndex}</strong>. The pipeline will map column headers to standard ERP fields in Step 4.
        </span>
      </div>

      {/* Footer Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          type="button"
          onClick={onBack}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '10px 18px',
            backgroundColor: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 500,
            color: '#334155',
            cursor: 'pointer',
          }}
        >
          <ArrowLeft size={16} /> Back
        </button>
        <button
          type="button"
          onClick={onNext}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '10px 24px',
            backgroundColor: '#0284c7',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Proceed to Column Mapping (SCR-008) <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}

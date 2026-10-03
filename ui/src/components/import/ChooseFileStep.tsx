import React, { useState, useRef } from 'react'
import { UploadCloud, FileSpreadsheet, AlertCircle, X, Download, HelpCircle, FileText } from 'lucide-react'
import { FileItem, SourceTypeId, SourceTypeOption } from './types'

interface ChooseFileStepProps {
  currentFile: FileItem | null
  sourceType: SourceTypeId
  onSelectFile: (file: FileItem) => void
  onChangeSourceType: (type: SourceTypeId) => void
  onNext: () => void
}

const SOURCE_OPTIONS: SourceTypeOption[] = [
  {
    id: 'd365_gl',
    label: 'Dynamics 365 GL export',
    description: 'General ledger transactions containing accounts, vouchers, debit/credit entries',
    recommendedExts: ['.xlsx', '.csv'],
  },
  {
    id: 'payroll',
    label: 'Payroll summary',
    description: 'Monthly payroll register by employee, cost center and earnings codes',
    recommendedExts: ['.xlsx', '.csv'],
  },
  {
    id: 'procurement_bank',
    label: 'Procurement / bank ledger',
    description: 'Vendor disbursements, bank statements and AP ledger postings',
    recommendedExts: ['.csv', '.xlsx'],
  },
  {
    id: 'budget',
    label: 'Budget',
    description: 'Approved annual or revised budget baseline by account and cost center',
    recommendedExts: ['.csv', '.xlsx'],
  },
  {
    id: 'master_data',
    label: 'Master data',
    description: 'Chart of accounts, vendor categories, cost centers, and threshold definitions',
    recommendedExts: ['.xlsx', '.csv'],
  },
]

// Preset samples matching the repository's sample-data folder
const SAMPLE_PRESETS: FileItem[] = [
  {
    id: 'sample-bank',
    name: 'bank_ledger_actuals.csv',
    path: 'sample-data/bank_ledger_actuals.csv',
    sizeBytes: 81803,
    format: 'csv',
    detectedSourceType: 'procurement_bank',
    sheetCount: 1,
    sheets: ['Default'],
    selectedSheet: 'Default',
    detectedDelimiter: ',',
    detectedEncoding: 'UTF-8',
    bannerDetected: true,
    bannerText: '# SAMPLE DATA — NOT FOR PRODUCTION USE',
    estimatedRows: 501,
    estimatedDurationSec: 0.8,
    headerRowIndex: 2,
    dataStartRowIndex: 3,
    isOverLimit: false,
    limitRows: 250000,
    importAnywayConfirmed: false,
  },
  {
    id: 'sample-gl',
    name: 'd365_gl_actuals.csv',
    path: 'sample-data/d365_gl_actuals.csv',
    sizeBytes: 50610576,
    format: 'csv',
    detectedSourceType: 'd365_gl',
    sheetCount: 1,
    sheets: ['GL_Extract'],
    selectedSheet: 'GL_Extract',
    detectedDelimiter: ',',
    detectedEncoding: 'UTF-8',
    bannerDetected: false,
    estimatedRows: 184502,
    estimatedDurationSec: 3.4,
    headerRowIndex: 1,
    dataStartRowIndex: 2,
    isOverLimit: false,
    limitRows: 250000,
    importAnywayConfirmed: false,
  },
  {
    id: 'sample-budget',
    name: 'budget_fy26.csv',
    path: 'sample-data/budget_fy26.csv',
    sizeBytes: 216583,
    format: 'csv',
    detectedSourceType: 'budget',
    sheetCount: 1,
    sheets: ['Budget2026'],
    selectedSheet: 'Budget2026',
    detectedDelimiter: ',',
    detectedEncoding: 'UTF-8',
    bannerDetected: false,
    estimatedRows: 2400,
    estimatedDurationSec: 1.1,
    headerRowIndex: 1,
    dataStartRowIndex: 2,
    isOverLimit: false,
    limitRows: 250000,
    importAnywayConfirmed: false,
  },
]

export const ChooseFileStep: React.FC<ChooseFileStepProps> = ({
  currentFile,
  sourceType,
  onSelectFile,
  onChangeSourceType,
  onNext,
}) => {
  const [isDragging, setIsDragging] = useState(false)
  const [fileQueue, setFileQueue] = useState<FileItem[]>(currentFile ? [currentFile] : [])
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [showHelpModal, setShowHelpModal] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const detectSourceTypeFromName = (name: string): SourceTypeId => {
    const lower = name.toLowerCase()
    if (lower.includes('gl') || lower.includes('d365') || lower.includes('ledger') && !lower.includes('bank')) return 'd365_gl'
    if (lower.includes('pay') || lower.includes('salary') || lower.includes('wage')) return 'payroll'
    if (lower.includes('bank') || lower.includes('procure') || lower.includes('ap')) return 'procurement_bank'
    if (lower.includes('budg') || lower.includes('target') || lower.includes('plan')) return 'budget'
    if (lower.includes('master') || lower.includes('coa') || lower.includes('account')) return 'master_data'
    return 'd365_gl'
  }

  const handleFilesAdded = (files: FileList | null) => {
    if (!files || files.length === 0) return
    const newItems: FileItem[] = []

    for (let i = 0; i < files.length; i++) {
      const f = files[i]
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase()
      if (!['.xlsx', '.xlsm', '.csv'].includes(ext)) {
        alert(`File format ${ext} is not supported. Please provide .xlsx, .xlsm, or .csv.`)
        continue
      }
      const detected = detectSourceTypeFromName(f.name)
      const isCsv = ext === '.csv'
      const item: FileItem = {
        id: `file-${Date.now()}-${i}`,
        name: f.name,
        path: f.name,
        sizeBytes: f.size,
        format: isCsv ? 'csv' : (ext === '.xlsm' ? 'xlsm' : 'xlsx'),
        detectedSourceType: detected,
        sheetCount: isCsv ? 1 : 3,
        sheets: isCsv ? ['Sheet1'] : ['ActiveActuals', 'Metadata', 'Summary'],
        selectedSheet: isCsv ? 'Sheet1' : 'ActiveActuals',
        detectedDelimiter: ',',
        detectedEncoding: 'UTF-8',
        bannerDetected: false,
        estimatedRows: Math.max(1, Math.round(f.size / 140)),
        estimatedDurationSec: Math.max(0.5, Number((f.size / 1000000 * 0.4).toFixed(1))),
        headerRowIndex: 1,
        dataStartRowIndex: 2,
        isOverLimit: f.size > 100000000,
        limitRows: 250000,
        importAnywayConfirmed: false,
      }
      newItems.push(item)
    }

    if (newItems.length > 0) {
      setFileQueue(prev => [...prev, ...newItems])
      onSelectFile(newItems[0])
      onChangeSourceType(newItems[0].detectedSourceType)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFilesAdded(e.dataTransfer.files)
  }

  const handleSelectPreset = (sample: FileItem) => {
    onSelectFile(sample)
    onChangeSourceType(sample.detectedSourceType)
    setFileQueue([sample])
  }

  const handleRemoveQueueItem = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const updated = fileQueue.filter(f => f.id !== id)
    setFileQueue(updated)
    if (currentFile?.id === id) {
      if (updated.length > 0) {
        onSelectFile(updated[0])
        onChangeSourceType(updated[0].detectedSourceType)
      }
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#0284c7', fontWeight: 700 }}>
            SCR-005 &bull; Step 1 of 6
          </span>
          <h2 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>
            Choose File &amp; Source Type
          </h2>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setShowTemplateModal(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              backgroundColor: '#f1f5f9',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 500,
              color: '#334155',
              cursor: 'pointer',
            }}
          >
            <Download size={14} /> Download a blank template ▾
          </button>
          <button
            type="button"
            onClick={() => setShowHelpModal(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              backgroundColor: '#f1f5f9',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 500,
              color: '#334155',
              cursor: 'pointer',
            }}
          >
            <HelpCircle size={14} /> What am I importing?
          </button>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={e => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: isDragging ? '2px dashed #0284c7' : '2px dashed #cbd5e1',
          backgroundColor: isDragging ? '#f0f9ff' : '#ffffff',
          borderRadius: '10px',
          padding: '40px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
          marginBottom: '20px',
          boxShadow: isDragging ? '0 0 0 4px rgba(2,132,199,0.1)' : 'none',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xlsm,.csv"
          multiple
          style={{ display: 'none' }}
          onChange={e => handleFilesAdded(e.target.files)}
        />
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
          <div style={{ backgroundColor: '#e0f2fe', padding: '14px', borderRadius: '50%', color: '#0284c7' }}>
            <UploadCloud size={32} />
          </div>
        </div>
        <div style={{ fontSize: '15px', fontWeight: 600, color: '#1e293b', marginBottom: '4px' }}>
          Drag this month's export here, or <span style={{ color: '#0284c7', textDecoration: 'underline' }}>Choose a file</span>
        </div>
        <div style={{ fontSize: '12px', color: '#64748b' }}>
          Supports <span style={{ fontWeight: 600, color: '#334155' }}>.xlsx</span>,{' '}
          <span style={{ fontWeight: 600, color: '#334155' }}>.xlsm</span>,{' '}
          <span style={{ fontWeight: 600, color: '#334155' }}>.csv</span> &bull; Multi-file queue supported
        </div>

        {/* Quick Sample File Pickers */}
        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px dashed #e2e8f0' }} onClick={e => e.stopPropagation()}>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>
            Or quickly test with repository sample files:
          </div>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
            {SAMPLE_PRESETS.map(sample => (
              <button
                key={sample.id}
                type="button"
                onClick={() => handleSelectPreset(sample)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: currentFile?.id === sample.id ? '1px solid #0284c7' : '1px solid #e2e8f0',
                  backgroundColor: currentFile?.id === sample.id ? '#e0f2fe' : '#f8fafc',
                  color: currentFile?.id === sample.id ? '#0369a1' : '#475569',
                  fontSize: '12px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                <FileSpreadsheet size={14} />
                {sample.name} ({formatFileSize(sample.sizeBytes)})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Selected File & Queue Section */}
      {currentFile && (
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FileSpreadsheet size={22} color="#0284c7" />
              <div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>{currentFile.name}</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  {formatFileSize(currentFile.sizeBytes)} &bull; {currentFile.format.toUpperCase()} &bull; ~{currentFile.estimatedRows.toLocaleString()} rows
                </div>
              </div>
            </div>
            <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '12px', backgroundColor: '#dcfce7', color: '#166534', fontWeight: 600 }}>
              Ready for pre-scan
            </span>
          </div>

          {/* Already Imported Variant */}
          {currentFile.isAlreadyImported && (
            <div style={{ marginTop: '10px', padding: '10px 14px', backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px', fontSize: '13px', color: '#92400e', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} />
                <span>
                  Already imported on <strong>{currentFile.alreadyImportedDate || '14-Sep-2026'}</strong> (batch #{currentFile.alreadyImportedBatch || 37})
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button type="button" style={{ fontSize: '12px', background: 'none', border: 'none', color: '#b45309', textDecoration: 'underline', cursor: 'pointer' }}>
                  View that import
                </button>
                <button type="button" style={{ fontSize: '12px', background: 'none', border: 'none', color: '#b45309', textDecoration: 'underline', cursor: 'pointer' }}>
                  Import a corrected file
                </button>
              </div>
            </div>
          )}

          {/* Multi-file queue list if > 1 */}
          {fileQueue.length > 1 && (
            <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid #f1f5f9' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '8px' }}>
                Batch Queue ({fileQueue.length} files queued)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {fileQueue.map((item, idx) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      onSelectFile(item)
                      onChangeSourceType(item.detectedSourceType)
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '6px 10px',
                      borderRadius: '4px',
                      backgroundColor: currentFile.id === item.id ? '#f0f9ff' : '#f8fafc',
                      border: currentFile.id === item.id ? '1px solid #bae6fd' : '1px solid #e2e8f0',
                      cursor: 'pointer',
                      fontSize: '12px',
                    }}
                  >
                    <span>
                      {idx + 1}. {item.name} ({formatFileSize(item.sizeBytes)})
                    </span>
                    <button
                      type="button"
                      onClick={e => handleRemoveQueueItem(item.id, e)}
                      style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '2px' }}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Source Type Selector */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>Source type:</div>
          <div style={{ fontSize: '12px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Detected from the file name — change it if wrong</span>
            <HelpCircle size={14} />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {SOURCE_OPTIONS.map(opt => {
            const isSelected = sourceType === opt.id
            return (
              <label
                key={opt.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '12px 14px',
                  borderRadius: '6px',
                  border: isSelected ? '1px solid #0284c7' : '1px solid #e2e8f0',
                  backgroundColor: isSelected ? '#f0f9ff' : '#ffffff',
                  cursor: 'pointer',
                  transition: 'background-color 0.1s ease',
                }}
              >
                <input
                  type="radio"
                  name="sourceType"
                  value={opt.id}
                  checked={isSelected}
                  onChange={() => onChangeSourceType(opt.id)}
                  style={{ marginTop: '3px' }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: isSelected ? '#0369a1' : '#1e293b' }}>
                    {opt.label}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>{opt.description}</div>
                </div>
              </label>
            )
          })}
        </div>
      </div>

      {/* Wizard Step Footer Actions */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
        <button
          type="button"
          onClick={onNext}
          disabled={!currentFile}
          style={{
            padding: '10px 24px',
            backgroundColor: currentFile ? '#0284c7' : '#94a3b8',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: currentFile ? 'pointer' : 'not-allowed',
          }}
        >
          Proceed to Pre-scan (SCR-006) &rarr;
        </button>
      </div>

      {/* Help Modal */}
      {showHelpModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setShowHelpModal(false)}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '520px',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>What am I importing?</h3>
              <button onClick={() => setShowHelpModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
            <p style={{ fontSize: '13px', color: '#475569', lineHeight: 1.5 }}>
              The FP&amp;A Month-End Copilot ingests transactional actuals and budget targets. Each source type maps to a specific schema required for deterministic BvA variance decomposition and exception detection.
            </p>
            <ul style={{ fontSize: '13px', color: '#334155', paddingLeft: '20px', lineHeight: 1.6 }}>
              <li><strong>Dynamics 365 GL:</strong> Ledger accounts, posting dates, debit/credit entries, dimensions.</li>
              <li><strong>Payroll summary:</strong> Departmental headcounts and salary/wage lines.</li>
              <li><strong>Procurement / bank ledger:</strong> Vendor disbursements and cash reconciliation entries.</li>
              <li><strong>Budget:</strong> Period-specific planned expenditure baseline.</li>
            </ul>
            <div style={{ textAlign: 'right', marginTop: '16px' }}>
              <button
                onClick={() => setShowHelpModal(false)}
                style={{ padding: '8px 16px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Download Template Modal */}
      {showTemplateModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setShowTemplateModal(false)}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '480px',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>Download Blank Templates</h3>
              <button onClick={() => setShowTemplateModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
            <p style={{ fontSize: '13px', color: '#475569', lineHeight: 1.5, marginBottom: '16px' }}>
              Select a standardized format template pre-configured with required headers and data types:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[
                { name: 'Dynamics 365 GL Actuals Template (.xlsx)', size: '14 KB' },
                { name: 'Bank Ledger Statement Template (.csv)', size: '8 KB' },
                { name: 'Annual Budget Baseline Template (.csv)', size: '12 KB' },
                { name: 'Chart of Accounts Master Template (.xlsx)', size: '18 KB' },
              ].map((item, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '10px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    fontSize: '13px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={16} color="#0284c7" />
                    <span>{item.name}</span>
                  </div>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>{item.size}</span>
                </div>
              ))}
            </div>
            <div style={{ textAlign: 'right', marginTop: '20px' }}>
              <button
                onClick={() => setShowTemplateModal(false)}
                style={{ padding: '8px 16px', backgroundColor: '#e2e8f0', color: '#334155', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px' }}
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

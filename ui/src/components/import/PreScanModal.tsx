import React, { useState } from 'react'
import { AlertTriangle, CheckCircle2, Clock, Database, Layers, ArrowLeft, ArrowRight, Settings } from 'lucide-react'
import { FileItem } from './types'

interface PreScanModalProps {
  file: FileItem
  onUpdateFile: (updated: Partial<FileItem>) => void
  onBack: () => void
  onNext: () => void
}

export const PreScanModal: React.FC<PreScanModalProps> = ({
  file,
  onUpdateFile,
  onBack,
  onNext,
}) => {
  const [selectedDelimiter, setSelectedDelimiter] = useState(file.detectedDelimiter || ',')
  const [selectedEncoding, setSelectedEncoding] = useState(file.detectedEncoding || 'UTF-8')
  const [isEditingDelimiter, setIsEditingDelimiter] = useState(false)
  const [importAnyway, setImportAnyway] = useState(file.importAnywayConfirmed || false)

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleDelimiterChange = (delim: string) => {
    setSelectedDelimiter(delim)
    onUpdateFile({ detectedDelimiter: delim })
  }

  const handleEncodingChange = (enc: string) => {
    setSelectedEncoding(enc)
    onUpdateFile({ detectedEncoding: enc })
  }

  const handleConfirmAnyway = (checked: boolean) => {
    setImportAnyway(checked)
    onUpdateFile({ importAnywayConfirmed: checked })
  }

  // Next is enabled if file is within limits OR if over-limit and "Import anyway" is checked
  const canProceed = !file.isOverLimit || importAnyway

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#0284c7', fontWeight: 700 }}>
          SCR-006 &bull; Step 2 of 6
        </span>
        <h2 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>
          File Pre-Scan &amp; Format Inspection
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
          Structural sanity probe: checking file boundaries, encoding, delimiters, and size limits before parsing.
        </p>
      </div>

      {/* Main Inspection Grid Card */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '24px', marginBottom: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '24px' }}>
          {/* File Spec */}
          <div style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#64748b', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Database size={14} /> File Size &amp; Path
            </div>
            <div style={{ fontSize: '15px', fontWeight: 700, marginTop: '6px', color: '#0f172a', wordBreak: 'break-all' }}>
              {file.name}
            </div>
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
              Size: <strong>{formatFileSize(file.sizeBytes)}</strong> &bull; Ext: <strong>.{file.format}</strong>
            </div>
          </div>

          {/* Row Estimates */}
          <div style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#64748b', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={14} /> Estimated Volume
            </div>
            <div style={{ fontSize: '20px', fontWeight: 700, marginTop: '4px', color: '#0284c7' }}>
              ~{file.estimatedRows.toLocaleString()} rows
            </div>
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
              Sheet count: <strong>{file.sheetCount}</strong> ({file.sheets.join(', ')})
            </div>
          </div>

          {/* Duration */}
          <div style={{ padding: '16px', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#64748b', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={14} /> Estimated Ingestion Time
            </div>
            <div style={{ fontSize: '20px', fontWeight: 700, marginTop: '4px', color: '#16a34a' }}>
              ~{file.estimatedDurationSec}s
            </div>
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
              Memory footprint: <strong>~{Math.max(4, Math.round(file.sizeBytes / (1024 * 1024) * 2.2))} MB</strong>
            </div>
          </div>
        </div>

        {/* Delimiter & Encoding Section */}
        <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '20px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#1e293b' }}>
              CSV Parser &amp; Character Encoding (FR-IMP-003)
            </div>
            <button
              type="button"
              onClick={() => setIsEditingDelimiter(!isEditingDelimiter)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                background: 'none',
                border: 'none',
                color: '#0284c7',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Settings size={14} /> {isEditingDelimiter ? 'Done' : 'Change Delimiter / Encoding'}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '20px', alignItems: 'center', fontSize: '13px', color: '#334155' }}>
            <div>
              Detected Delimiter: <span style={{ fontFamily: 'monospace', fontWeight: 700, backgroundColor: '#f1f5f9', padding: '2px 6px', borderRadius: '4px' }}>
                {selectedDelimiter === ',' ? 'Comma (,)' : selectedDelimiter === ';' ? 'Semicolon (;)' : selectedDelimiter === '\t' ? 'Tab (\\t)' : selectedDelimiter}
              </span>
            </div>
            <div>
              Detected Encoding: <span style={{ fontFamily: 'monospace', fontWeight: 700, backgroundColor: '#f1f5f9', padding: '2px 6px', borderRadius: '4px' }}>
                {selectedEncoding}
              </span>
            </div>
          </div>

          {isEditingDelimiter && (
            <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#f8fafc', borderRadius: '6px', display: 'flex', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>
                  Override Delimiter:
                </label>
                <select
                  value={selectedDelimiter}
                  onChange={e => handleDelimiterChange(e.target.value)}
                  style={{ padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                >
                  <option value=",">Comma (,)</option>
                  <option value=";">Semicolon (;)</option>
                  <option value="\t">Tab (\t)</option>
                  <option value="|">Pipe (|)</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>
                  Override Encoding:
                </label>
                <select
                  value={selectedEncoding}
                  onChange={e => handleEncodingChange(e.target.value)}
                  style={{ padding: '6px 10px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                >
                  <option value="UTF-8">UTF-8</option>
                  <option value="UTF-16LE">UTF-16 LE</option>
                  <option value="ISO-8859-1">ISO-8859-1 (Latin-1)</option>
                  <option value="windows-1252">Windows-1252</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Banner Presence Detection */}
        <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '20px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#1e293b', marginBottom: '8px' }}>
            Metadata &amp; Header Banner Analysis
          </div>
          {file.bannerDetected ? (
            <div style={{ padding: '12px 14px', backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', fontSize: '13px', color: '#1e40af' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
                <CheckCircle2 size={16} /> Non-data metadata banner detected at Row 1
              </div>
              <div style={{ marginTop: '4px', fontFamily: 'monospace', fontSize: '12px', color: '#3b82f6', backgroundColor: '#ffffff', padding: '6px 8px', borderRadius: '4px', border: '1px solid #dbeafe' }}>
                {file.bannerText || '# SAMPLE DATA — NOT FOR PRODUCTION USE'}
              </div>
              <div style={{ marginTop: '6px', fontSize: '12px', color: '#1d4ed8' }}>
                Row 1 will be treated as non-data comment/banner. Header picker in Step 3 will automatically target Row 2.
              </div>
            </div>
          ) : (
            <div style={{ padding: '10px 14px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', fontSize: '13px', color: '#166534', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={16} /> No intrusive metadata banners detected; column headers start cleanly at Row 1.
            </div>
          )}
        </div>
      </div>

      {/* Limits Check: Normal vs Over-limit Amber Block */}
      {file.isOverLimit ? (
        <div style={{ backgroundColor: '#fffbeb', border: '2px solid #fde68a', borderRadius: '8px', padding: '18px 20px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            <AlertTriangle size={24} color="#d97706" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#92400e' }}>
                Warning: File exceeds recommended row limit threshold
              </div>
              <div style={{ fontSize: '13px', color: '#b45309', marginTop: '4px', lineHeight: 1.5 }}>
                Estimated rows (<strong>{file.estimatedRows.toLocaleString()}</strong>) exceed standard threshold (<strong>{file.limitRows.toLocaleString()}</strong>).
                Consequence: Memory usage will be elevated (~150MB) and parsing will take longer.
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px', cursor: 'pointer', fontSize: '13px', fontWeight: 600, color: '#78350f' }}>
                <input
                  type="checkbox"
                  checked={importAnyway}
                  onChange={e => handleConfirmAnyway(e.target.checked)}
                />
                Import anyway — I confirm that I want to process this large dataset.
              </label>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', color: '#166534', fontSize: '13px', marginBottom: '24px' }}>
          <CheckCircle2 size={16} />
          <span>Limit check passed: File size and row count are within normal limits (250,000 row safety threshold).</span>
        </div>
      )}

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
          disabled={!canProceed}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '10px 24px',
            backgroundColor: canProceed ? '#0284c7' : '#94a3b8',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: canProceed ? 'pointer' : 'not-allowed',
          }}
        >
          Proceed to Sheet &amp; Header Picker (SCR-007) <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}

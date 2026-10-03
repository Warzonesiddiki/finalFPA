export type SourceTypeId = 'd365_gl' | 'payroll' | 'procurement_bank' | 'budget' | 'master_data'

export interface SourceTypeOption {
  id: SourceTypeId
  label: string
  description: string
  recommendedExts: string[]
}

export interface FileItem {
  id: string
  name: string
  path: string
  sizeBytes: number
  format: 'csv' | 'xlsx' | 'xlsm'
  detectedSourceType: SourceTypeId
  sheetCount: number
  sheets: string[]
  selectedSheet: string
  detectedDelimiter: string
  detectedEncoding: string
  bannerDetected: boolean
  bannerText?: string
  estimatedRows: number
  estimatedDurationSec: number
  headerRowIndex: number // 1-indexed
  dataStartRowIndex: number // 1-indexed
  isOverLimit: boolean
  limitRows: number
  importAnywayConfirmed: boolean
  isAlreadyImported?: boolean
  alreadyImportedBatch?: number
  alreadyImportedDate?: string
}

export interface TargetFieldDef {
  code: string
  label: string
  required: boolean
  description: string
}

export interface ColumnMappingItem {
  sourceColumn: string
  targetField: string
  sampleValues: string[]
  confidence: number
  isAutoMatched: boolean
  required: boolean
  override?: {
    dateFormat?: string
    numberScale?: number
    invertSign?: boolean
    trimWhitespace?: boolean
  }
}

export interface OffenderItem {
  code: string
  name: string
  severity: 'error' | 'quarantine' | 'warning' | 'skipped'
  sheet?: string
  row?: number
  cell?: string
  sampleValue?: string
  reason: string
}

export interface ValidationSummary {
  stage: 'prescan' | 'parse' | 'validate' | 'stage' | 'commit'
  percent: number
  elapsedSec: number
  etaSec: number
  status: 'idle' | 'running' | 'completed' | 'cancelled' | 'rejected'
  counts: {
    errors: number
    quarantined: number
    warnings: number
    skipped: number
    passed: number
  }
  offenders: OffenderItem[]
}

export interface CommitResultData {
  batchId: number
  fileName: string
  archiveFileName: string
  totalSourceRows: number
  loadedCount: number
  quarantinedCount: number
  rejectedCount: number
  isBalanced: boolean
  totalDebit: string
  totalCredit: string
  netImbalance: string
  dataQualityScore: number
  failedChecksCount: number
  committedAt: string
}

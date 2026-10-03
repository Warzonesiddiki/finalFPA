export interface BvaItem {
  statementLine: string
  accountId: number
  accountCode: string
  accountName: string
  accountType: string
  favourabilityDirection: string
  actualAmount: string
  budgetAmount: string
  varianceAmount: string
  variancePct: string | null
  favourability: 'favourable' | 'unfavourable' | 'neutral'
}

export interface StatementLineSummary {
  statementLine: string
  actualAmount: string
  budgetAmount: string
  varianceAmount: string
  variancePct: string | null
  favourability: 'favourable' | 'unfavourable' | 'neutral'
  accountCount: number
}

export interface DrillRow {
  actualId: number
  importBatchId: number
  sourceFileName: string
  sourceRowRef: string
  postingDate: string
  voucherNo: string
  lineNo: number
  invoiceNo: string | null
  description: string | null
  debit: string
  credit: string
  netAmount: string
  companyCode: string
  accountCode: string
  accountName: string
  statementLine: string
  costCenterCode: string | null
}

export interface FilterState {
  periodId: number | null
  window: 'MTD' | 'YTD'
  companyId: number | null
  costCenterId: number | null
  statementLine: string | null
  searchQuery: string
}

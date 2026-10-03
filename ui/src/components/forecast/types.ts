export type ScenarioType = 'base' | 'best' | 'worst';
export type ForecastMethod = 'run_rate' | 'remaining_budget' | 'avg_3m' | 'manual' | 'not_forecast';

export interface ForecastLineDTO {
  account_id: number;
  account_code: string;
  account_name: string;
  statement_line: string;
  account_group: string;
  method_used: string;
  is_manual_override: boolean;
  override_reason: string | null;
  period_amounts: Record<string, string>; // e.g. "FY26-P10" -> "1031933.67"
  fy_landing: string;
  is_eligible: boolean;
  ineligibility_reason: string | null;
}

export interface ForecastWorkspaceData {
  scenario: string;
  versionId: string;
  versionNo: number;
  status: string;
  isLocked: boolean;
  closedPeriods: string[];
  openPeriods: string[];
  lastGeneratedAt: string;
  generatedBy: string;
  lines: ForecastLineDTO[];
  totals: Record<string, string>;
}

export interface ScenarioCompareRow {
  accountId: number;
  accountCode: string;
  accountName: string;
  statementLine: string;
  base: string;
  best: string;
  worst: string;
}

export interface ForecastAccuracyReportData {
  accountGroup: string;
  methodId: string;
  periodCount: number;
  zeroPeriodsExcluded: number;
  signedError: string;
  absoluteError: string;
  signedBias: string;
  mapeLite: string | null;
  guidanceNote: string;
}

/**
 * Exceptions register domain types per 08_UI_UX_SPEC.md (SCR-023..SCR-026)
 * and 02_FUNCTIONAL_SPEC.md (FR-EXC family).
 */

export type SeverityLevel = 'High' | 'Medium' | 'Low';

export type ExceptionStatus = 
  | 'open'
  | 'in_review'
  | 'explained'
  | 'corrected'
  | 'closed'
  | 'reopened'
  | 'not_applicable';

export type AgingBucket = '0-7' | '8-30' | '31+';

export interface ExceptionItem {
  exception_id: number;
  identity_hash: string;
  rule_id: string;
  rule_name: string;
  severity: SeverityLevel;
  status: ExceptionStatus;
  owner_name: string;
  owner_role: string;
  period_code: string;
  period_id?: number | null;
  subject_key: string;
  subject_display: string;
  amount_at_risk: string;
  effective_threshold: string;
  days_open: number;
  aging_bucket: AgingBucket;
  is_overdue: boolean;
  overdue_days: number;
  flagged_again: boolean;
  evidence_count: number;
  notes_count: number;
  first_seen_date: string;
  last_seen_date: string;
  created_at: string;
  updated_at: string;
}

export interface ExceptionNote {
  noteId: number;
  author: string;
  noteText: string;
  createdAt: string;
}

export interface ExceptionEvent {
  eventId: number;
  eventType: string;
  fromValue?: string | null;
  toValue?: string | null;
  noteText?: string | null;
  actor: string;
  occurredAt: string;
}

export interface ExceptionDetailResponse {
  exception: ExceptionItem;
  sampleRows: Record<string, any>[];
  evidenceRefs: string[];
  notes: ExceptionNote[];
  events: ExceptionEvent[];
}

export interface ExceptionsRegisterSummary {
  total: number;
  open: number;
  overdue: number;
  high: number;
}

export interface ExceptionsListResponse {
  items: ExceptionItem[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
  summary: ExceptionsRegisterSummary;
}

export interface ExceptionFilterState {
  period: string;
  severity: string;
  status: string;
  owner: string;
  ruleId: string;
  agingBucket: string;
  search: string;
}

export interface PackRefDTO {
  pack_id: number;
  pack_token: 'excel' | 'ppt' | 'both';
  pack_version: number;
  file_name: string;
  file_path: string;
  file_size_bytes: number;
  period_code: string;
  scenario_id: string;
  generated_at: string;
  generated_by: string;
  status: string;
}

export interface IssuanceRefDTO {
  issue_id: number;
  period_id: number;
  period_code: string;
  pack_version: number;
  pack_type: string;
  issued_at: string;
  issued_by: string;
  recipients: string[];
  snapshot_id: number | null;
  file_names: string[];
  status: 'issued' | 'superseded';
  notes: string | null;
}

export interface CommentaryRowDTO {
  commentary_id: number;
  period_id: number;
  scope_type: 'line' | 'executive';
  subject_key: string;
  current_version_no: number;
  locked_by_issue_id: number | null;
  text: string;
  source: 'user' | 'ai' | 'rule_based';
  author: string;
  is_locked: boolean;
}

export interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  organization?: string;
  job_title?: string;
  phone_number?: string;
  custom_fields?: Record<string, any>;
  tags?: string[];
  notes?: string;
  is_archived: boolean;
  consent_status?: string;
  consent_timestamp?: string;
  consent_source?: string;
  unsubscribe_timestamp?: string;
  is_suppressed: boolean;
  source?: string;
  created_at: string;
  updated_at: string;
}

export interface ContactGroup {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface ContactImport {
  id: string;
  file_name: string;
  total_records: number;
  successful_records: number;
  updated_records: number;
  skipped_records: number;
  failed_records: number;
  column_mapping?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface ContactCreate {
  first_name: string;
  last_name: string;
  email: string;
  organization?: string;
  job_title?: string;
  phone_number?: string;
  custom_fields?: Record<string, any>;
  tags?: string[];
  notes?: string;
  consent_status?: string;
  consent_source?: string;
}

export interface ContactUpdate {
  first_name?: string;
  last_name?: string;
  email?: string;
  organization?: string;
  job_title?: string;
  phone_number?: string;
  custom_fields?: Record<string, any>;
  tags?: string[];
  notes?: string;
  is_archived?: boolean;
  consent_status?: string;
  consent_source?: string;
  is_suppressed?: boolean;
}

export interface ContactGroupCreate {
  name: string;
  description?: string;
}

export interface ContactGroupUpdate {
  name?: string;
  description?: string;
}

export interface SearchContactsRequest {
  query?: string;
  tags?: string[];
  group_id?: string;
  include_archived?: boolean;
}

export interface CSVImportRequest {
  column_mapping: Record<string, string>;
  skip_duplicates: boolean;
  update_existing: boolean;
}

export interface PersonalizationPreviewRequest {
  html_content: string;
  contact_id: string;
}

export interface PersonalizationPreviewResponse {
  personalized_html: string;
  missing_variables: string[];
}

export interface RecipientSelectionRequest {
  recipient_ids: string[];
  group_ids: string[];
  manual_emails: string[];
}

export interface RecipientSummaryResponse {
  total_recipients: number;
  duplicate_count: number;
  invalid_recipients: string[];
  missing_personalization_fields: Record<string, string[]>;
  recipient_sources: Record<string, number>;
}
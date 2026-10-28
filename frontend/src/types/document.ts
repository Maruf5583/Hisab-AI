export type DocumentType = 'sales_invoice' | 'purchase_invoice' | 'payment_receipt' | 'voucher' | 'unknown';
export type DocumentStatus = 'uploaded' | 'processing' | 'needs_review' | 'approved' | 'rejected' | 'posted';

export interface DocumentBlock {
  bbox: [number, number, number, number];
  text: string;
  confidence?: number;
}

export interface DocumentPage {
  id: string;
  page_number: number;
  width?: number | null;
  height?: number | null;
  has_native_text: boolean;
  raw_text?: string | null;
  ocr_data?: {
    provider?: string;
    confidence?: number;
    blocks?: DocumentBlock[];
  } | null;
}

export interface DocumentExtraction {
  id: string;
  document_id: string;
  document_type_candidate?: DocumentType | null;
  party_name_candidate?: string | null;
  matched_party_id?: string | null;
  document_number_candidate?: string | null;
  issue_date_candidate?: string | null;
  due_date_candidate?: string | null;
  subtotal_candidate?: string | null;
  tax_amount_candidate?: string | null;
  total_amount_candidate?: string | null;
  paid_amount_candidate?: string | null;
  due_amount_candidate?: string | null;
  confidence_score?: string | null;
  warnings?: string[] | null;
  is_human_corrected: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: string;
  business_id: string;
  uploaded_by_user_id?: string | null;
  original_filename: string;
  file_hash_sha256: string;
  mime_type: string;
  file_size_bytes: number;
  page_count: number;
  document_type: DocumentType;
  status: DocumentStatus;
  rejection_reason?: string | null;
  created_at: string;
  updated_at: string;
  pages?: DocumentPage[];
  extraction?: DocumentExtraction;
}

import { apiRequest } from './client';
import { DocumentItem, DocumentPage, DocumentExtraction } from '../types/document';

export interface PaginatedDocuments {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DocumentApprovalPayload {
  document_type: string;
  party_id: string;
  document_number: string;
  issue_date: string;
  due_date?: string | null;
  subtotal: string;
  tax_amount: string;
  total_amount: string;
  paid_amount?: string;
  notes?: string;
}

export interface DocumentPostingResponse {
  success: boolean;
  document_id: string;
  document_status: string;
  invoice_id?: string | null;
  payment_id?: string | null;
  ledger_entry_ids: string[];
  total_posted_debit: string;
  total_posted_credit: string;
  message: string;
}

export const documentApi = {
  list: async (params?: { status?: string; document_type?: string; search?: string; page?: number; page_size?: number }): Promise<PaginatedDocuments> => {
    const q = new URLSearchParams();
    if (params?.status) q.append('status', params.status);
    if (params?.document_type) q.append('document_type', params.document_type);
    if (params?.search) q.append('search', params.search);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());

    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<PaginatedDocuments>(`/documents/${queryStr}`);
  },

  get: async (id: string): Promise<DocumentItem> => {
    return apiRequest<DocumentItem>(`/documents/${id}`);
  },

  upload: async (file: File, documentType?: string): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append('file', file);
    if (documentType) {
      formData.append('document_type', documentType);
    }

    return apiRequest<DocumentItem>('/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  process: async (id: string): Promise<DocumentItem> => {
    return apiRequest<DocumentItem>(`/documents/${id}/process`, {
      method: 'POST',
    });
  },

  getPages: async (id: string): Promise<DocumentPage[]> => {
    return apiRequest<DocumentPage[]>(`/documents/${id}/pages`);
  },

  updateExtraction: async (id: string, data: Partial<DocumentExtraction>): Promise<DocumentExtraction> => {
    return apiRequest<DocumentExtraction>(`/documents/${id}/extraction`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  reject: async (id: string, reason: string): Promise<DocumentItem> => {
    return apiRequest<DocumentItem>(`/documents/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  post: async (id: string, approval: DocumentApprovalPayload): Promise<DocumentPostingResponse> => {
    return apiRequest<DocumentPostingResponse>(`/documents/${id}/post`, {
      method: 'POST',
      body: JSON.stringify(approval),
    });
  },

  getDownloadUrl: (id: string): string => {
    return `/api/v1/documents/${id}/download`;
  },
};

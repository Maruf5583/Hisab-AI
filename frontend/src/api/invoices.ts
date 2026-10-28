import { apiRequest } from './client';
import { Invoice } from '../types/accounting';

export interface PaginatedInvoices {
  items: Invoice[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface InvoiceCreateData {
  party_id: string;
  invoice_type: 'sales' | 'purchase';
  invoice_number: string;
  issue_date: string;
  due_date?: string | null;
  subtotal?: string;
  tax_amount?: string;
  total_amount: string;
  notes?: string;
  items?: Array<{
    description: string;
    quantity: number;
    unit_price: number;
    line_total: number;
    tax_rate?: number;
  }>;
}

export const invoiceApi = {
  list: async (params?: {
    invoice_type?: string;
    status?: string;
    party_id?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedInvoices> => {
    const q = new URLSearchParams();
    if (params?.invoice_type) q.append('invoice_type', params.invoice_type);
    if (params?.status) q.append('status', params.status);
    if (params?.party_id) q.append('party_id', params.party_id);
    if (params?.start_date) q.append('start_date', params.start_date);
    if (params?.end_date) q.append('end_date', params.end_date);
    if (params?.search) q.append('search', params.search);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());

    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<PaginatedInvoices>(`/invoices/${queryStr}`);
  },

  get: async (id: string): Promise<Invoice> => {
    return apiRequest<Invoice>(`/invoices/${id}`);
  },

  create: async (data: InvoiceCreateData): Promise<Invoice> => {
    return apiRequest<Invoice>('/invoices/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  reverse: async (id: string): Promise<Invoice> => {
    return apiRequest<Invoice>(`/invoices/${id}/reverse`, {
      method: 'POST',
    });
  },
};

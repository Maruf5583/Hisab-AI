import { apiRequest } from './client';
import { Payment } from '../types/accounting';

export interface PaginatedPayments {
  items: Payment[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PaymentCreateData {
  party_id: string;
  payment_type: 'customer_receipt' | 'supplier_payment';
  payment_method: 'cash' | 'bank' | 'bkash' | 'nagad' | 'other';
  payment_date: string;
  amount: string;
  reference_number?: string;
  notes?: string;
}

export interface PaymentAllocateItem {
  invoice_id: string;
  allocated_amount: string;
}

export const paymentApi = {
  list: async (params?: {
    payment_type?: string;
    payment_method?: string;
    party_id?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedPayments> => {
    const q = new URLSearchParams();
    if (params?.payment_type) q.append('payment_type', params.payment_type);
    if (params?.payment_method) q.append('payment_method', params.payment_method);
    if (params?.party_id) q.append('party_id', params.party_id);
    if (params?.start_date) q.append('start_date', params.start_date);
    if (params?.end_date) q.append('end_date', params.end_date);
    if (params?.search) q.append('search', params.search);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());

    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<PaginatedPayments>(`/payments/${queryStr}`);
  },

  get: async (id: string): Promise<Payment> => {
    return apiRequest<Payment>(`/payments/${id}`);
  },

  create: async (data: PaymentCreateData): Promise<Payment> => {
    return apiRequest<Payment>('/payments/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  allocate: async (paymentId: string, allocations: PaymentAllocateItem[]): Promise<Payment> => {
    return apiRequest<Payment>(`/payments/${paymentId}/allocate`, {
      method: 'POST',
      body: JSON.stringify({ allocations }),
    });
  },

  downloadPdf: async (id: string): Promise<void> => {
    const token = localStorage.getItem('hisabai_token');
    const activeBizId = localStorage.getItem('hisabai_active_business_id');
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (activeBizId) headers['X-Business-Id'] = activeBizId;

    const res = await fetch(`/api/v1/payments/${id}/pdf`, { headers });
    if (!res.ok) throw new Error('Failed to download payment receipt PDF');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Receipt-${id.slice(0, 8)}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },
};

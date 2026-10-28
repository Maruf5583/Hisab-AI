import { apiRequest } from './client';
import { LedgerEntry } from '../types/accounting';

export interface AgingBucket {
  amount: string;
  invoice_count: number;
}

export interface PartyAgingDetail {
  party_id: string;
  party_name: string;
  phone?: string | null;
  bucket_0_15: string;
  bucket_16_30: string;
  bucket_31_60: string;
  bucket_60_plus: string;
  total_due: string;
}

export interface AgingReportResponse {
  report_type: 'receivables' | 'payables';
  as_of_date: string;
  total_due: string;
  summary_0_15: AgingBucket;
  summary_16_30: AgingBucket;
  summary_31_60: AgingBucket;
  summary_60_plus: AgingBucket;
  party_details: PartyAgingDetail[];
}

export interface CashbookReport {
  start_date: string;
  end_date: string;
  opening_cash: string;
  total_inflow: string;
  total_outflow: string;
  closing_cash: string;
  entries: LedgerEntry[];
}

export interface VatSummaryResponse {
  start_date?: string;
  end_date?: string;
  output_vat_collected: string;
  input_vat_paid: string;
  net_vat_payable: string;
}

export interface DashboardSummary {
  total_receivable: string;
  total_payable: string;
  cash_in_hand: string;
  bank_balance: string;
  pending_documents_count: number;
}

export const reportsApi = {
  getReceivablesAging: async (as_of?: string): Promise<AgingReportResponse> => {
    const q = as_of ? `?as_of=${as_of}` : '';
    return apiRequest<AgingReportResponse>(`/reports/receivables-aging${q}`);
  },

  getPayablesAging: async (as_of?: string): Promise<AgingReportResponse> => {
    const q = as_of ? `?as_of=${as_of}` : '';
    return apiRequest<AgingReportResponse>(`/reports/payables-aging${q}`);
  },

  getCashbook: async (start_date?: string, end_date?: string): Promise<CashbookReport> => {
    const q = new URLSearchParams();
    if (start_date) q.append('start_date', start_date);
    if (end_date) q.append('end_date', end_date);
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<CashbookReport>(`/reports/cashbook${queryStr}`);
  },

  getVatSummary: async (start_date?: string, end_date?: string): Promise<VatSummaryResponse> => {
    const q = new URLSearchParams();
    if (start_date) q.append('start_date', start_date);
    if (end_date) q.append('end_date', end_date);
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<VatSummaryResponse>(`/reports/vat-summary${queryStr}`);
  },

  getDashboardSummary: async (): Promise<DashboardSummary> => {
    return apiRequest<DashboardSummary>('/reports/dashboard-summary');
  },
};

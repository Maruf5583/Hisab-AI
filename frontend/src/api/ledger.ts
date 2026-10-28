import { apiRequest } from './client';
import { LedgerEntry } from '../types/accounting';

export interface PaginatedLedger {
  items: LedgerEntry[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TrialBalanceAccount {
  account_name: string;
  total_debit: string;
  total_credit: string;
  net_balance: string;
}

export interface TrialBalanceResponse {
  as_of_date: string;
  accounts: TrialBalanceAccount[];
  grand_total_debit: string;
  grand_total_credit: string;
  is_balanced: boolean;
  difference: string;
}

export const ledgerApi = {
  list: async (params?: {
    account_name?: string;
    transaction_type?: string;
    party_id?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedLedger> => {
    const q = new URLSearchParams();
    if (params?.account_name) q.append('account_name', params.account_name);
    if (params?.transaction_type) q.append('transaction_type', params.transaction_type);
    if (params?.party_id) q.append('party_id', params.party_id);
    if (params?.start_date) q.append('start_date', params.start_date);
    if (params?.end_date) q.append('end_date', params.end_date);
    if (params?.search) q.append('search', params.search);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());

    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<PaginatedLedger>(`/ledger/${queryStr}`);
  },

  getTrialBalance: async (as_of?: string): Promise<TrialBalanceResponse> => {
    const queryStr = as_of ? `?as_of=${as_of}` : '';
    return apiRequest<TrialBalanceResponse>(`/ledger/trial-balance${queryStr}`);
  },
};

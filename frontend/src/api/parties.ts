import { apiRequest } from './client';
import { Party, PartyBalance } from '../types/party';
import { LedgerEntry } from '../types/accounting';

export interface PaginatedParties {
  items: Party[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export const partyApi = {
  list: async (params?: { party_type?: string; search?: string; page?: number; page_size?: number }): Promise<PaginatedParties> => {
    const q = new URLSearchParams();
    if (params?.party_type) q.append('party_type', params.party_type);
    if (params?.search) q.append('search', params.search);
    if (params?.page) q.append('page', params.page.toString());
    if (params?.page_size) q.append('page_size', params.page_size.toString());
    
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<PaginatedParties>(`/parties/${queryStr}`);
  },

  get: async (partyId: string): Promise<Party> => {
    return apiRequest<Party>(`/parties/${partyId}`);
  },

  create: async (data: {
    name: string;
    party_type: 'buyer' | 'supplier' | 'both';
    phone?: string;
    email?: string;
    address?: string;
    tax_id?: string;
    opening_balance?: string;
    opening_balance_type?: 'receivable' | 'payable';
  }): Promise<Party> => {
    return apiRequest<Party>('/parties/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getBalance: async (partyId: string): Promise<PartyBalance> => {
    return apiRequest<PartyBalance>(`/parties/${partyId}/balance`);
  },

  getLedger: async (partyId: string): Promise<LedgerEntry[]> => {
    return apiRequest<LedgerEntry[]>(`/parties/${partyId}/ledger`);
  },
};

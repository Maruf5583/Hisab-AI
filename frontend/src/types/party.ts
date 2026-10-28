export type PartyType = 'buyer' | 'supplier' | 'both';
export type OpeningBalanceType = 'receivable' | 'payable';

export interface Party {
  id: string;
  business_id: string;
  name: string;
  party_type: PartyType;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  tax_id?: string | null;
  opening_balance: string;
  opening_balance_type: OpeningBalanceType;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PartyBalance {
  party_id: string;
  party_name: string;
  party_type: PartyType;
  opening_balance: string;
  opening_balance_type: OpeningBalanceType;
  total_invoiced: string;
  total_paid: string;
  current_balance: string;
  balance_type: 'receivable' | 'payable' | 'zero';
}

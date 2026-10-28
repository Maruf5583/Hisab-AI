export interface LedgerEntry {
  id: string;
  business_id: string;
  transaction_type: string;
  reference_id: string;
  entry_date: string;
  account_name: string;
  debit: string;
  credit: string;
  party_id?: string | null;
  description?: string | null;
  is_reversal: boolean;
  created_at: string;
}

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  tax_rate: number;
}

export interface Invoice {
  id: string;
  business_id: string;
  party_id: string;
  party_name?: string;
  invoice_type: 'sales' | 'purchase';
  invoice_number: string;
  issue_date: string;
  due_date?: string | null;
  subtotal: string;
  tax_amount: string;
  total_amount: string;
  paid_amount: string;
  due_amount: string;
  status: 'draft' | 'approved' | 'partially_paid' | 'paid' | 'reversed';
  notes?: string | null;
  items?: InvoiceItem[];
  created_at: string;
}

export interface Payment {
  id: string;
  business_id: string;
  party_id: string;
  party_name?: string;
  payment_type: 'customer_receipt' | 'supplier_payment';
  payment_method: 'cash' | 'bank' | 'bkash' | 'nagad' | 'other';
  payment_date: string;
  amount: string;
  allocated_amount: string;
  unapplied_amount: string;
  reference_number?: string | null;
  status: 'draft' | 'approved' | 'posted' | 'reversed';
  created_at: string;
}

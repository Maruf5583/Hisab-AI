export interface Business {
  id: string;
  name: string;
  slug: string;
  legal_name?: string | null;
  tax_id?: string | null;
  currency: string;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BusinessMember {
  id: string;
  business_id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: 'owner' | 'accountant' | 'reviewer' | 'viewer';
  is_active: boolean;
  created_at: string;
}

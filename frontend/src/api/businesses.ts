import { apiRequest } from './client';
import { Business, BusinessMember } from '../types/business';

export const businessApi = {
  list: async (): Promise<Business[]> => {
    return apiRequest<Business[]>('/businesses/');
  },

  get: async (businessId: string): Promise<Business> => {
    return apiRequest<Business>(`/businesses/${businessId}`);
  },

  create: async (data: { name: string; slug: string; currency?: string; legal_name?: string }): Promise<Business> => {
    return apiRequest<Business>('/businesses/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  listMembers: async (businessId: string): Promise<BusinessMember[]> => {
    return apiRequest<BusinessMember[]>(`/businesses/${businessId}/members`);
  },

  addMember: async (businessId: string, email: string, role: string): Promise<BusinessMember> => {
    return apiRequest<BusinessMember>(`/businesses/${businessId}/members`, {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    });
  },
};

import { apiRequest } from './client';
import { User, TokenResponse } from '../types/auth';

export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    return apiRequest<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  register: async (data: { email: string; password: string; full_name: string; phone?: string }): Promise<User> => {
    return apiRequest<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getMe: async (): Promise<User> => {
    return apiRequest<User>('/auth/me');
  },
};

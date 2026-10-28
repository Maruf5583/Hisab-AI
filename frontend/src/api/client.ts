const API_BASE = '/api/v1';

export interface ApiError {
  status: number;
  message: string;
  detail?: any;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('hisabai_token');
  const activeBusinessId = localStorage.getItem('hisabai_active_business_id');

  const headers: Record<string, string> = {
    'Accept': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (activeBusinessId) {
    headers['X-Business-Id'] = activeBusinessId;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorDetail = '';
      try {
        const errJson = await res.json();
        errorDetail = errJson.detail || JSON.stringify(errJson);
      } catch {
        errorDetail = res.statusText || 'An error occurred';
      }

      const err: ApiError = {
        status: res.status,
        message: typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail),
        detail: errorDetail,
      };
      throw err;
    }

    if (res.status === 204) {
      return {} as T;
    }

    return (await res.json()) as T;
  } catch (error) {
    if ((error as ApiError).status) {
      throw error;
    }
    throw {
      status: 0,
      message: (error as Error).message || 'Network connection failed. Backend might be unreachable.',
    } as ApiError;
  }
}

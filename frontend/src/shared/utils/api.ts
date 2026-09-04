interface RequestOptions extends RequestInit {
  params?: Record<string, string | number>;
}

export const api = async (endpoint: string, options: RequestOptions = {}) => {
  const token = localStorage.getItem('token');
  const baseUrl = import.meta.env?.VITE_API_URL || 'http://localhost:8000';
  const fullEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  let urlStr = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) + fullEndpoint : baseUrl + fullEndpoint;
  const url = new URL(urlStr);

  if (options.params) {
    Object.entries(options.params).forEach(([key, value]) => {
      url.searchParams.append(key, String(value));
    });
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  if (options.headers) {
    Object.assign(headers, options.headers);
  }

  const response = await fetch(url.toString(), {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.message || `API error: ${response.statusText}`);
  }

  return response.json();
};

export const apiClient = {
  get: (endpoint: string, options?: RequestOptions) => api(endpoint, { ...options, method: 'GET' }),
  post: (endpoint: string, data?: any, options?: RequestOptions) => api(endpoint, { ...options, method: 'POST', body: JSON.stringify(data) }),
  put: (endpoint: string, data?: any, options?: RequestOptions) => api(endpoint, { ...options, method: 'PUT', body: JSON.stringify(data) }),
  patch: (endpoint: string, data?: any, options?: RequestOptions) => api(endpoint, { ...options, method: 'PATCH', body: JSON.stringify(data) }),
  delete: (endpoint: string, options?: RequestOptions) => api(endpoint, { ...options, method: 'DELETE' }),
};

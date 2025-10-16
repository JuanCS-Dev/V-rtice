/**
 * Centralized API Client
 * Uses API Gateway (8000) as single entry point
 * Governed by: Constituição Vértice v2.7
 */

const API_BASE = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

const request = async (endpoint, options = {}) => {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    if (error.message.includes('API Error')) {
      throw error;
    }
    throw new Error(`Network error: ${error.message}`);
  }
};

export const apiClient = {
  get: (endpoint, options = {}) =>
    request(endpoint, { ...options, method: 'GET' }),

  post: (endpoint, data = {}, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    }),

  put: (endpoint, data = {}, options = {}) =>
    request(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (endpoint, options = {}) =>
    request(endpoint, { ...options, method: 'DELETE' }),

  request,
};

export const directClient = {
  async request(baseUrl, path, options = {}) {
    const url = `${baseUrl}${path}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error.message.includes('API Error')) {
        throw error;
      }
      throw new Error(`Network error: ${error.message}`);
    }
  },
};

export const getWebSocketUrl = (endpoint) => {
  const wsBase = API_BASE.replace(/^http/, 'ws');
  return `${wsBase}${endpoint}${endpoint.includes('?') ? '&' : '?'}api_key=${API_KEY}`;
};

export default apiClient;

/**
 * VAPT Agent API Client
 */
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token from localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auth refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

// ── Projects ──────────────────────────────────────────────────────────────────
export const projectsAPI = {
  list: () => api.get('/projects'),
  create: (data: { name: string; description?: string; client_name?: string }) =>
    api.post('/projects', data),
  get: (id: string) => api.get(`/projects/${id}`),
  update: (id: string, data: object) => api.put(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
};

// ── Targets ───────────────────────────────────────────────────────────────────
export const targetsAPI = {
  list: (projectId: string) => api.get(`/projects/${projectId}/targets`),
  create: (projectId: string, data: object) =>
    api.post(`/projects/${projectId}/targets`, data),
  get: (id: string) => api.get(`/targets/${id}`),
  update: (id: string, data: object) => api.put(`/targets/${id}`, data),
  delete: (id: string) => api.delete(`/targets/${id}`),
};

// ── Scopes ────────────────────────────────────────────────────────────────────
export const scopesAPI = {
  get: (targetId: string) => api.get(`/targets/${targetId}/scope`),
  create: (targetId: string, data: object) =>
    api.post(`/targets/${targetId}/scope`, data),
  update: (targetId: string, data: object) =>
    api.put(`/targets/${targetId}/scope`, data),
  check: (targetId: string, url: string, method: string) =>
    api.post(`/targets/${targetId}/scope/check`, { url, method }),
};

// ── Scans ─────────────────────────────────────────────────────────────────────
export const scansAPI = {
  list: (targetId?: string) =>
    api.get('/scans', { params: targetId ? { target_id: targetId } : {} }),
  create: (data: { target_id: string; scan_type?: string; config?: object }) =>
    api.post('/scans', data),
  get: (id: string) => api.get(`/scans/${id}`),
  cancel: (id: string) => api.post(`/scans/${id}/cancel`),
};

// ── HTTP History ──────────────────────────────────────────────────────────────
export const httpHistoryAPI = {
  list: (params?: object) => api.get('/http-history', { params }),
  get: (id: string) => api.get(`/http-history/${id}`),
  getBody: (id: string, part: 'request' | 'response') =>
    api.get(`/http-history/${id}/body`, { params: { part } }),
};

// ── Repeater ──────────────────────────────────────────────────────────────────
export const repeaterAPI = {
  execute: (data: object) => api.post('/repeater', data),
  getBody: (id: string) => api.get(`/repeater/${id}/body`),
};

// ── Findings ──────────────────────────────────────────────────────────────────
export const findingsAPI = {
  list: (params?: object) => api.get('/findings', { params }),
  get: (id: string) => api.get(`/findings/${id}`),
  getEvidence: (id: string) => api.get(`/findings/${id}/evidence`),
  validate: (id: string) => api.post(`/findings/${id}/validate`),
};

// ── Endpoints / App Map ───────────────────────────────────────────────────────
export const endpointsAPI = {
  list: (params?: object) => api.get('/endpoints', { params }),
  getAppMap: (targetId: string) => api.get(`/targets/${targetId}/app-map`),
  getAuthProfiles: (targetId: string) => api.get(`/targets/${targetId}/auth-profiles`),
  createAuthProfile: (targetId: string, data: object) =>
    api.post(`/targets/${targetId}/auth-profiles`, data),
};

// ── AI ────────────────────────────────────────────────────────────────────────
export const aiAPI = {
  chat: (data: { message: string; scan_id?: string; finding_id?: string }) =>
    api.post('/ai/chat', data),
  analyze: (data: { scan_id: string; focus?: string }) =>
    api.post('/ai/analyze', data),
};

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsAPI = {
  list: () => api.get('/reports'),
  create: (data: { scan_id: string; format: string; title?: string }) =>
    api.post('/reports', data),
  get: (id: string) => api.get(`/reports/${id}`),
  download: (id: string) =>
    api.get(`/reports/${id}/download`, { responseType: 'blob' }),
};

/**
 * Unified API client — all frontend HTTP calls go through here.
 * Auto-injects Authorization header from localStorage.
 */

const API_BASE = '/api';
const BACKEND_URL = 'http://localhost:8001';

function getBaseUrl(): string {
  // SSR: Node.js fetch needs absolute URL; relative URLs don't work
  if (typeof window === 'undefined') return BACKEND_URL;
  // Client: relative path goes through Next.js proxy in dev, or same-origin in prod
  return '';
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T = any>(method: string, path: string, body?: any, retries = 1): Promise<T> {
  const url = `${getBaseUrl()}${API_BASE}${path}`;

  let res: Response;
  try {
    res = await fetch(url, {
      method,
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...authHeaders(),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  } catch (networkErr: any) {
    if (retries > 0) {
      await new Promise(r => setTimeout(r, 500));
      return request<T>(method, path, body, retries - 1);
    }
    throw new Error(`无法连接到服务器 — 请确认后端已启动 (${networkErr.message || 'network error'})`);
  }

  // Retry on 5xx server errors (transient backend issues)
  if (res.status >= 500 && res.status < 600 && retries > 0) {
    await new Promise(r => setTimeout(r, 500));
    return request<T>(method, path, body, retries - 1);
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}: ${res.statusText}` }));
    throw new Error(err.detail || `请求失败 (${res.status})`);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json();
}

export function apiGet<T = any>(path: string): Promise<T> {
  return request<T>('GET', path);
}

export function apiPost<T = any>(path: string, body?: any): Promise<T> {
  return request<T>('POST', path, body);
}

export function apiPut<T = any>(path: string, body?: any): Promise<T> {
  return request<T>('PUT', path, body);
}

export function apiDelete(path: string): Promise<void> {
  return request<void>('DELETE', path);
}

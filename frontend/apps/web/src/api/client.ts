import { notification } from 'antd';
import React from 'react';

const API_URL = import.meta.env.VITE_API_URL || '/api';

export interface ApiErrorResponse {
  code: string;
  message: string;
  details: string;
  traceId: string;
}

export class ApiClientError extends Error {
  constructor(public data: ApiErrorResponse) {
    super(data.message);
    this.name = 'ApiClientError';
  }
}

export class ApiClient {
  static async request(endpoint: string, options: RequestInit = {}) {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {})
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let res: Response;
    try {
      res = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
    } catch (err: any) {
      // Network error (backend down, cors, etc)
      const errData: ApiErrorResponse = {
        code: 'NET-001',
        message: 'Unable to connect to the server.',
        details: err.message,
        traceId: 'local-' + Date.now()
      };
      throw new ApiClientError(errData);
    }

    if (!res.ok) {
      let errData: any;
      try {
        const body = await res.json();
        errData = body.error || body.detail?.error || body.detail;
      } catch (e) {
        errData = {
          code: `HTTP-${res.status}`,
          message: 'An unexpected server error occurred.',
          details: res.statusText,
          traceId: 'unknown'
        };
      }
      if (!errData || typeof errData === 'string') {
        errData = {
          code: `HTTP-${res.status}`,
          message: typeof errData === 'string' ? errData : 'An unexpected server error occurred.',
          details: res.statusText,
          traceId: 'unknown'
        };
      }
      throw new ApiClientError(errData);
    }
    return res.json();
  }

  static async get(endpoint: string) { return this.request(endpoint); }
  static async post(endpoint: string, body: unknown) {
    return this.request(endpoint, { method: 'POST', body: JSON.stringify(body) });
  }
  static async put(endpoint: string, body: unknown) {
    return this.request(endpoint, { method: 'PUT', body: JSON.stringify(body) });
  }
  static async delete(endpoint: string) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  static handleError(err: unknown) {
    if (err instanceof ApiClientError) {
      notification.error({
        message: err.data.message,
        description: `Code: ${err.data.code} | Trace: ${err.data.traceId}`,
        duration: 10
      });
    } else {
      notification.error({
        message: 'Unexpected Error',
        description: String(err),
        duration: 10
      });
    }
  }
}

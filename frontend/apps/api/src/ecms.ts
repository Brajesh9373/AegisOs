import { ApiError } from './errors.js';

/**
 * Typed client for the ECMS Python backend, the system of record for
 * project discovery, live DSH agent hierarchy, and workspace execution.
 *
 * The BFF owns browser auth (requireAuth) and calls ECMS service-to-service:
 * the shared ECMS_SERVICE_TOKEN goes out as `x-ecms-service-token`, which
 * ECMS trusts without a browser session. Upstream failures surface as
 * ApiError with the ECMS status/detail preserved, so the frontend sees one
 * error shape no matter which backend answered.
 */

const ECMS_BACKEND_URL = (process.env.ECMS_BACKEND_URL || 'http://localhost:8000').replace(/\/+$/, '');
const ECMS_SERVICE_TOKEN = process.env.ECMS_SERVICE_TOKEN || '';

export interface EcmsCallOptions {
  method?: string;
  body?: unknown;
  /** Forwarded browser bearer token (ECMS validates it when no service token matches). */
  authorization?: string;
}

export async function ecms<T>(path: string, options: EcmsCallOptions = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (options.authorization) headers['Authorization'] = options.authorization;
  if (ECMS_SERVICE_TOKEN) headers['x-ecms-service-token'] = ECMS_SERVICE_TOKEN;

  const init: RequestInit = { method: options.method || 'GET', headers };
  if (init.method !== 'GET' && init.method !== 'HEAD' && options.body !== undefined) {
    init.body = JSON.stringify(options.body);
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${ECMS_BACKEND_URL}${path}`, init);
  } catch (err: any) {
    throw new ApiError(502, 'ECMS-UNREACHABLE', 'Workspace backend is unreachable.', String(err?.message || err));
  }

  const text = await upstream.text();
  if (!upstream.ok) {
    let detail: any = text.slice(0, 500);
    try {
      const parsed = JSON.parse(text);
      detail = (parsed as any)?.detail || (parsed as any)?.error || detail;
    } catch {
      /* keep raw text */
    }
    throw new ApiError(upstream.status, 'ECMS-UPSTREAM', 'Workspace backend request failed.', detail);
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError(502, 'ECMS-BAD-RESPONSE', 'Workspace backend returned non-JSON.', text.slice(0, 200));
  }
}

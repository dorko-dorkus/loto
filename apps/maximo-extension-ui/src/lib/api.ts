/**
 * Helper to prefix API requests with the configured base URL.
 *
 * Uses the `NEXT_PUBLIC_API_BASE` environment variable if set.
 */
import { toastError } from './toast';

const ERROR_MESSAGES: Record<string, string> = {
  VALIDATION_ERROR: 'Request validation failed',
  IMPORT_ERROR: 'Unable to import requested resource',
  GENERATION_ERROR: 'Failed to generate response',
};

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const base = process.env.NEXT_PUBLIC_API_BASE ?? '';
  const token = process.env.NEXT_PUBLIC_API_TOKEN;
  const headers = new Headers(init?.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  const res = await fetch(`${base}${path}`, { ...init, headers });
  if (!res.ok) {
    try {
      const data = (await res.clone().json()) as { code?: string };
      const msg = data.code && ERROR_MESSAGES[data.code];
      if (msg) toastError(msg);
    } catch {
      /* ignore */
    }
  }
  return res;
}

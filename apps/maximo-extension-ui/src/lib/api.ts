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
  SIMULATION_RED: 'Simulation must be green to commit',
  POLICY_CHIPS_MISSING: 'Please accept all policy chips',
};

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const base = process.env.NEXT_PUBLIC_API_BASE ?? '';
  const headers = new Headers(init?.headers || {});
  const token =
    typeof window !== 'undefined' ? window.localStorage.getItem('token') : null;
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

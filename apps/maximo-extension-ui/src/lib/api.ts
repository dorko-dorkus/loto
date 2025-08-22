/**
 * Helper to prefix API requests with the configured base URL.
 *
 * Uses the `NEXT_PUBLIC_API_BASE` environment variable if set.
 */
export function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const base = process.env.NEXT_PUBLIC_API_BASE ?? '';
  const token = process.env.NEXT_PUBLIC_API_TOKEN;
  const headers = new Headers(init?.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(`${base}${path}`, { ...init, headers });
}

import { describe, it, expect, vi, afterEach } from 'vitest';
import { apiFetch } from './api';

const originalFetch = global.fetch;

afterEach(() => {
  global.fetch = originalFetch;
  delete process.env.NEXT_PUBLIC_API_TOKEN;
});

describe('apiFetch', () => {
  it('adds authorization header when token is set', async () => {
    const mock = vi.fn().mockResolvedValue(new Response());
    global.fetch = mock as any;
    process.env.NEXT_PUBLIC_API_TOKEN = 'token';

    await apiFetch('/test');

    const headers = mock.mock.calls[0][1].headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer token');
  });

  it('does not override existing authorization header', async () => {
    const mock = vi.fn().mockResolvedValue(new Response());
    global.fetch = mock as any;
    process.env.NEXT_PUBLIC_API_TOKEN = 'token';

    await apiFetch('/test', { headers: { Authorization: 'Bearer existing' } });

    const headers = mock.mock.calls[0][1].headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer existing');
  });
});


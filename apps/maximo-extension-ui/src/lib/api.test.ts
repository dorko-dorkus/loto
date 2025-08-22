import { describe, it, expect, vi, afterEach } from 'vitest';

vi.mock('./toast', () => ({ toastError: vi.fn() }));
import { apiFetch } from './api';
import { toastError } from './toast';

const originalFetch = global.fetch;

afterEach(() => {
  global.fetch = originalFetch;
  delete process.env.NEXT_PUBLIC_API_TOKEN;
  vi.clearAllMocks();
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

  it('shows banner for known error codes', async () => {
    const body = JSON.stringify({ code: 'VALIDATION_ERROR' });
    const mock = vi
      .fn()
      .mockResolvedValue(
        new Response(body, {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        })
      );
    global.fetch = mock as any;

    await apiFetch('/test');

    expect(toastError).toHaveBeenCalledWith('Request validation failed');
  });
});


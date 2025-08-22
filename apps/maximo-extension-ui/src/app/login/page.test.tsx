import { render, fireEvent, waitFor } from '@testing-library/react';
import { expect, test, vi, afterEach } from 'vitest';
import Page from './page';

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));

const originalFetch = global.fetch;

afterEach(() => {
  global.fetch = originalFetch;
  window.localStorage.clear();
});

test('stores token on successful login', async () => {
  global.fetch = vi
    .fn()
    .mockResolvedValue(new Response(JSON.stringify({ access_token: 'abc' }), { status: 200 }));
  const { getByText, getByLabelText } = render(<Page />);
  fireEvent.change(getByLabelText('Username'), { target: { value: 'u' } });
  fireEvent.change(getByLabelText('Password'), { target: { value: 'p' } });
  fireEvent.click(getByText('Login'));
  await waitFor(() => expect(window.localStorage.getItem('token')).toBe('abc'));
});

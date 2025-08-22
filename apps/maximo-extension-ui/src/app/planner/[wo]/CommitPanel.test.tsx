import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { test, expect, vi, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CommitPanel from './CommitPanel';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

test('renders audit metadata and disables commit in TEST role', async () => {
  vi.stubEnv('NEXT_PUBLIC_ROLE', 'TEST');
  vi.stubEnv('NEXT_PUBLIC_USE_API', 'true');
  const blueprint = { diff: 'diff text', audit_metadata: { user: 'alice' } };
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(blueprint) }));
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <CommitPanel wo="WO-1" />
    </QueryClientProvider>
  );
  await screen.findByTestId('diff');
  expect(screen.getByText(/Audit Metadata/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Commit' })).toBeDisabled();
});

test('requires typing COMMIT to confirm', async () => {
  vi.stubEnv('NEXT_PUBLIC_ROLE', 'DEV');
  vi.stubEnv('NEXT_PUBLIC_USE_API', 'true');
  const blueprint = { diff: 'diff text' };
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(blueprint) })
    .mockResolvedValue({ ok: true });
  vi.stubGlobal('fetch', fetchMock);
  const prompt = vi.spyOn(window, 'prompt').mockReturnValue('nope');
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <CommitPanel wo="WO-1" />
    </QueryClientProvider>
  );
  await screen.findByTestId('diff');
  const button = screen.getByRole('button', { name: 'Commit' });
  fireEvent.click(button);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  prompt.mockReturnValue('COMMIT');
  fireEvent.click(button);
  expect(fetchMock).toHaveBeenCalledTimes(2);
  prompt.mockRestore();
});

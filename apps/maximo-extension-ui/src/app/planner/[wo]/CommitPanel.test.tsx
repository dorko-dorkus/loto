import { render, screen } from '@testing-library/react';
import { test, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CommitPanel from './CommitPanel';

test('renders audit metadata and disables commit in TEST role', async () => {
  vi.stubEnv('NEXT_PUBLIC_ROLE', 'TEST');
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
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

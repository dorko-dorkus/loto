import { render, screen, fireEvent, cleanup, act } from '@testing-library/react';
import { test, expect, vi, afterEach, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as toast from '../../../lib/toast';
import CommitPanel from './CommitPanel';

beforeEach(() => {
  vi.stubGlobal('alert', vi.fn());
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
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
      <CommitPanel wo="WO-1" simOk />
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
    .mockResolvedValue(new Response(null, { status: 204 }));
  vi.stubGlobal('fetch', fetchMock);
  const prompt = vi.spyOn(window, 'prompt').mockReturnValue('nope');
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <CommitPanel wo="WO-1" simOk />
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

test('shows banner when policies missing', async () => {
  vi.stubEnv('NEXT_PUBLIC_ROLE', 'DEV');
  vi.stubEnv('NEXT_PUBLIC_USE_API', 'true');
  const blueprint = { diff: 'diff text' };
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(blueprint) })
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({ code: 'POLICY_CHIPS_MISSING' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        }
      )
    );
  vi.stubGlobal('fetch', fetchMock);
  const toastSpy = vi.spyOn(toast, 'toastError');
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <CommitPanel wo="WO-1" simOk />
    </QueryClientProvider>
  );
  await screen.findByRole('button', { name: 'Commit' });
  vi.spyOn(window, 'prompt').mockReturnValue('COMMIT');
  const button = screen.getByRole('button', { name: 'Commit' });
  await act(async () => {
    fireEvent.click(button);
  });
  expect(toastSpy).toHaveBeenCalledWith('Please accept all policy chips');
});

test('shows banner when simulation red', async () => {
  vi.stubEnv('NEXT_PUBLIC_ROLE', 'DEV');
  vi.stubEnv('NEXT_PUBLIC_USE_API', 'true');
  const blueprint = { diff: 'diff text' };
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(blueprint) })
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({ code: 'SIMULATION_RED' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        }
      )
    );
  vi.stubGlobal('fetch', fetchMock);
  const toastSpy = vi.spyOn(toast, 'toastError');
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <CommitPanel wo="WO-1" simOk={false} />
    </QueryClientProvider>
  );
  await screen.findByRole('button', { name: 'Commit' });
  vi.spyOn(window, 'prompt').mockReturnValue('COMMIT');
  const button = screen.getByRole('button', { name: 'Commit' });
  await act(async () => {
    fireEvent.click(button);
  });
  expect(toastSpy).toHaveBeenCalledWith('Simulation must be green to commit');
});

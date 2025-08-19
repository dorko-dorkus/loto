import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, afterEach, test, expect, vi } from 'vitest';
import ReactivePicker from './ReactivePicker';

const mockHats = [
  { hat_id: 'h1', c_r: 0.8, rotation: 1 },
  { hat_id: 'h2', c_r: 0.6 }
];

beforeEach(() => {
  vi.spyOn(global, 'fetch').mockResolvedValue({
    ok: true,
    json: async () => mockHats
  } as any);
});

afterEach(() => {
  vi.restoreAllMocks();
});

test('renders hats with rotation penalty highlighted', async () => {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <ReactivePicker wo="100" />
    </QueryClientProvider>
  );
  await waitFor(() => screen.getByText(/h1/));
  expect(screen.getByText(/h1/)).toBeInTheDocument();
  expect(screen.getByText(/rotation penalty/)).toBeInTheDocument();
});


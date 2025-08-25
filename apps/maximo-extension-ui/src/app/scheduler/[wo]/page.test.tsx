import { fireEvent, render, screen } from '@testing-library/react';
import { vi, test, expect } from 'vitest';
import Page from './page';

test('renders virtualized gantt and updates conflicts', async () => {
  class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  // @ts-ignore
  global.ResizeObserver = ResizeObserver;

  vi.stubEnv('NEXT_PUBLIC_USE_API', 'true');
  const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? '';

  const sample = {
    schedule: [
      {
        date: '2024-01-01',
        p10: 10,
        p50: 20,
        p90: 30,
        price: 40,
        hats: 1,
        conflicts: ['Conflict 0']
      },
      {
        date: '2024-01-02',
        p10: 12,
        p50: 22,
        p90: 32,
        price: 42,
        hats: 2,
        conflicts: []
      }
    ],
    seed: 'abc',
    objective: 0.95,
    blocked_by_parts: false,
    rulepack_sha256: 'abc123'
  };
  const fetchMock = vi
    .spyOn(global, 'fetch')
    .mockImplementation((input: RequestInfo) => {
      if (typeof input === 'string' && input === apiBase + '/schedule') {
        return Promise.resolve({ ok: true, json: async () => sample } as Response);
      }
      if (typeof input === 'string' && input === apiBase + '/hats') {
        return Promise.resolve({ ok: true, json: async () => [] } as Response);
      }
      return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
    });

  render(<Page params={{ wo: 'WO-1' }} />);
  const rows = await screen.findAllByTestId('gantt-row-date');
  fireEvent.click(rows[0]);
  expect(screen.getByLabelText('Conflict 0')).toBeInTheDocument();
  fetchMock.mockRestore();
});


import { render, screen } from '@testing-library/react';
import { vi, test, expect } from 'vitest';
import Page from './page';

test('renders gantt, price curve and hats timeline', async () => {
  class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  // @ts-ignore
  global.ResizeObserver = ResizeObserver;

  const sample = {
    schedule: [
      { date: '2024-01-01', p10: 10, p50: 20, p90: 30, price: 40, hats: 1 },
      { date: '2024-01-02', p10: 12, p50: 22, p90: 32, price: 42, hats: 2 }
    ],
    seed: 'abc',
    objective: 0.95
  };
  const fetchMock = vi
    .spyOn(global, 'fetch')
    .mockImplementation((input: RequestInfo) => {
      if (typeof input === 'string' && input === '/schedule') {
        return Promise.resolve({ ok: true, json: async () => sample } as Response);
      }
      if (typeof input === 'string' && input === '/api/hats') {
        return Promise.resolve({ ok: true, json: async () => [] } as Response);
      }
      return Promise.resolve({ ok: true, json: async () => ({}) } as Response);
    });

  const { container } = render(<Page params={{ wo: 'WO-1' }} />);

  await screen.findByTestId('gantt-chart');
  expect(screen.getByTestId('price-chart')).toBeInTheDocument();
  expect(screen.getByTestId('hats-chart')).toBeInTheDocument();
  expect(screen.getByTestId('schedule-meta').textContent).toContain('Seed: abc');
  expect(screen.getByTestId('schedule-meta').textContent).toContain('Objective: 0.95');
  expect(container.firstChild).toMatchSnapshot();
  const synced = document.querySelectorAll('[data-sync="schedule"]');
  expect(synced.length).toBe(3);
  fetchMock.mockRestore();
});


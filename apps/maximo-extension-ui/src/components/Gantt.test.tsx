import { render } from '@testing-library/react';
import { describe, expect, test } from 'vitest';
import Gantt from './Gantt';

const sample = [
  { date: '2024-01-01', p10: 10, p50: 20, p90: 30, price: 40, hats: 1 },
  { date: '2024-01-02', p10: 12, p50: 22, p90: 32, price: 42, hats: 2 }
];

describe('Gantt', () => {
  test('maps sync id across charts', () => {
    class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    // @ts-ignore
    global.ResizeObserver = ResizeObserver;
    const { getByTestId } = render(<Gantt data={sample} />);
    expect(getByTestId('gantt-chart').getAttribute('data-sync')).toBe('schedule');
    expect(getByTestId('price-chart').getAttribute('data-sync')).toBe('schedule');
    expect(getByTestId('hats-chart').getAttribute('data-sync')).toBe('schedule');
  });
});

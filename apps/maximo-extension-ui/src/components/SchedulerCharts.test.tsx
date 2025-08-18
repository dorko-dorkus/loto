import { render, screen } from '@testing-library/react';
import { SchedulerTooltip } from './SchedulerCharts';
import { test, expect } from 'vitest';

test('scheduler tooltip displays values', () => {
  const payload = [
    {
      payload: { date: '2024-01-01', p10: 10, p50: 20, p90: 30, price: 25, derate: 5 }
    }
  ];
  render(<SchedulerTooltip active label="2024-01-01" payload={payload} />);
  expect(screen.getByText('P10: 10')).toBeInTheDocument();
  expect(screen.getByText('P50: 20')).toBeInTheDocument();
  expect(screen.getByText('P90: 30')).toBeInTheDocument();
  expect(screen.getByText('Price: 25')).toBeInTheDocument();
  expect(screen.getByText('Derate: 5')).toBeInTheDocument();
});

import { render, screen } from '@testing-library/react';
import { test, expect } from 'vitest';
import HatsTimeline, { HatLane } from './HatsTimeline';

test('shows rank badge and labelled tooltip', () => {
  const lanes: HatLane[] = [
    { id: 'a', rank: 1, cr: 5, c: 4, r: 3, kpis: [1, 2, 3, 4, 5] }
  ];
  render(<HatsTimeline lanes={lanes} />);
  expect(screen.getByText('1')).toBeInTheDocument();
  const tooltip = screen.getByRole('tooltip', { name: /cr 5/ });
  expect(tooltip).toBeInTheDocument();
});

import { render, screen } from '@testing-library/react';
import { test, expect } from 'vitest';
import KpiCards from './KpiCards';

const kpis = [
  { label: 'Active', value: 1 },
  { label: 'Completed', value: 2 }
];

test('renders KPI labels', () => {
  render(<KpiCards items={kpis} />);
  expect(screen.getByText('Active')).toBeInTheDocument();
  expect(screen.getByText('Completed')).toBeInTheDocument();
});

test('matches snapshot', () => {
  const { container } = render(<KpiCards items={kpis} />);
  expect(container.firstChild).toMatchSnapshot();
});


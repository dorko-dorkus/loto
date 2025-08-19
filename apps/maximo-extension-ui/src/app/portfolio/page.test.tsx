import { render, screen, within } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders work orders from mock fetch', async () => {
  render(<Page />);
  await screen.findAllByText('Pump replacement');
  const rowgroups = screen.getAllByRole('rowgroup');
  const tbody = rowgroups[rowgroups.length - 1];
  const rows = within(tbody).getAllByRole('row');
  expect(rows).toHaveLength(3);
});

test('row actions preserve seed/objective in links', async () => {
  window.history.pushState({}, '', '/portfolio?seed=abc&objective=0.5');
  render(<Page />);
  await screen.findAllByText('Pump replacement');
  const rowgroups = screen.getAllByRole('rowgroup');
  const tbody = rowgroups[rowgroups.length - 1];
  const [first] = within(tbody).getAllByRole('row');
  const planner = within(first).getByRole('link', { name: 'Planner' });
  const scheduler = within(first).getByRole('link', { name: 'Scheduler' });
  expect(planner).toHaveAttribute(
    'href',
    '/planner/WO-1?seed=abc&objective=0.5'
  );
  expect(scheduler).toHaveAttribute(
    'href',
    '/scheduler/WO-1?seed=abc&objective=0.5'
  );
});

import { render, screen } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders 5 tabs', async () => {
  render(<Page params={{ wo: 'WO-1' }} />);
  const tabs = await screen.findAllByRole('tab');
  expect(tabs).toHaveLength(5);
});

test('renders export buttons', () => {
  render(<Page params={{ wo: 'WO-1' }} />);
  expect(screen.getAllByText('Export PDF').length).toBeGreaterThan(0);
  expect(screen.getAllByText('Export JSON').length).toBeGreaterThan(0);
});

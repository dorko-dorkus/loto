import { render, screen, within } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders work orders from mock fetch', async () => {
  render(<Page />);
  await screen.findByText('Pump replacement');
  const [, tbody] = screen.getAllByRole('rowgroup');
  const rows = within(tbody).getAllByRole('row');
  expect(rows).toHaveLength(3);
});

import { render, fireEvent } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders candidate table and toggles selection', () => {
  const { getAllByRole } = render(<Page />);
  const checkboxes = getAllByRole('checkbox') as HTMLInputElement[];
  expect(checkboxes.length).toBeGreaterThan(0);
  const first = checkboxes[0];
  expect(first.checked).toBe(false);
  fireEvent.click(first);
  expect(first.checked).toBe(true);
});

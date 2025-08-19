import { render, screen, fireEvent } from '@testing-library/react';
import { test, expect } from 'vitest';
import DensityToggle from './DensityToggle';

test('toggles between comfortable and compact densities', async () => {
  render(<DensityToggle />);
  const button = screen.getByRole('button', { name: /density/i });
  expect(document.documentElement.dataset.density).toBe('comfortable');
  fireEvent.click(button);
  expect(document.documentElement.dataset.density).toBe('compact');
  fireEvent.click(button);
  expect(document.documentElement.dataset.density).toBe('comfortable');
});

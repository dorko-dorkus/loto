import { render, screen } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders portfolio', async () => {
  render(<Page />);
  expect(await screen.findByText('Portfolio')).toBeInTheDocument();
});

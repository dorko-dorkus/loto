import { render, screen } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders 4 tabs', async () => {
  render(<Page params={{ wo: 'WO-1' }} />);
  const tabs = await screen.findAllByRole('tab');
  expect(tabs).toHaveLength(4);
});

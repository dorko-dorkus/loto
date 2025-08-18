import { render } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders 4 tabs', () => {
  const { getAllByRole } = render(<Page params={{ wo: 'WO-1' }} />);
  expect(getAllByRole('tab')).toHaveLength(4);
});

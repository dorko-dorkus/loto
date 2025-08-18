import { render, waitFor } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders blueprint rows from mock', async () => {
  const { getAllByRole } = render(<Page />);
  await waitFor(() => expect(getAllByRole('row')).toHaveLength(4));
});

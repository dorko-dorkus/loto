import { render } from '@testing-library/react';
import { test, expect } from 'vitest';
import Page from './page';

test('renders page', () => {
  const { container } = render(<Page />);
  expect(container.querySelector('main')).not.toBeNull();
});

import { render } from '@testing-library/react';
import { test, expect } from 'vitest';
import Button from './Button';

test('matches snapshot', () => {
  const { container } = render(<Button>Click</Button>);
  expect(container.firstChild).toMatchSnapshot();
});

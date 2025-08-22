import { render } from '@testing-library/react';
import { expect, test } from 'vitest';
import Stepper from './Stepper';

test('matches snapshot', () => {
  const { container } = render(
    <Stepper steps={['Step 1', 'Step 2', 'Step 3']} active={1} />
  );
  expect(container.firstChild).toMatchSnapshot();
});

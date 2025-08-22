import { render } from '@testing-library/react';
import { expect, test } from 'vitest';
import WizardExport from './WizardExport';

test('matches snapshot', () => {
  const { container } = render(<WizardExport plan={{}} />);
  expect(container.firstChild).toMatchSnapshot();
});

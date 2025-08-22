import { render } from '@testing-library/react';
import { test, expect } from 'vitest';
import WizardReview from './WizardReview';

test('highlights missing required fields', () => {
  const files = [
    {
      name: 'test.csv',
      data: [
        { required: '', optional: 'ok' }
      ]
    }
  ];
  const { container } = render(
    <WizardReview
      files={files}
      requiredFields={['required']}
      accepted={false}
      setAccepted={() => {}}
    />
  );
  const errorCell = container.querySelector('td.bg-red-100');
  expect(errorCell).not.toBeNull();
});


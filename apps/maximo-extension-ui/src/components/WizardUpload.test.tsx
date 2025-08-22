import { render, fireEvent, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import WizardUpload from './WizardUpload';

test('supports multiple csv uploads and parsing', async () => {
  const setData = vi.fn();
  const { getByTestId } = render(<WizardUpload setData={setData} />);
  const input = getByTestId('wizard-upload-input') as HTMLInputElement;

  expect(input.multiple).toBe(true);

  const file1 = new File(['a,b\n1,2'], 'one.csv', { type: 'text/csv' });
  const file2 = new File(['c,d\n3,4'], 'two.csv', { type: 'text/csv' });

  fireEvent.change(input, { target: { files: [file1, file2] } });

  await waitFor(() =>
    expect(setData).toHaveBeenCalledWith([
      { name: 'one.csv', data: [{ a: '1', b: '2' }] },
      { name: 'two.csv', data: [{ c: '3', d: '4' }] }
    ])
  );

  expect(localStorage.getItem('wizardUpload')).toBe(
    JSON.stringify([
      { name: 'one.csv', data: [{ a: '1', b: '2' }] },
      { name: 'two.csv', data: [{ c: '3', d: '4' }] }
    ])
  );
});


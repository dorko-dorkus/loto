import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { test, expect } from 'vitest';
import ConflictsList from './ConflictsList';

test('click sets recommended items', async () => {
  const candidates = [
    { id: '1', label: 'Candidate 1', explanation: 'First option' },
    { id: '2', label: 'Candidate 2', explanation: 'Second option' },
    { id: '3', label: 'Candidate 3', explanation: 'Third option' }
  ];
  const { container } = render(<ConflictsList candidates={candidates} />);
  fireEvent.click(screen.getByText('Select recommended set'));
  await waitFor(() => {
    expect(screen.getByLabelText('Candidate 1')).toBeChecked();
    expect(screen.getByLabelText('Candidate 3')).toBeChecked();
  });
  expect(container.firstChild).toMatchSnapshot();
});

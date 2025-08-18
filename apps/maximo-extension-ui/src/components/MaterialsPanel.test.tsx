import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { test, expect, afterEach } from 'vitest';
import MaterialsPanel from './MaterialsPanel';

const items = [
  { item: 'Widget', required: 1, onHand: 0, eta: 'tomorrow', status: 'short' as const }
];

afterEach(() => cleanup());

test('renders workflow buttons with aria labels', () => {
  render(<MaterialsPanel items={items} />);
  expect(screen.getByLabelText('Raise RFQ')).toBeInTheDocument();
  expect(screen.getByLabelText('Issue pick list')).toBeInTheDocument();
  expect(screen.getByLabelText('Park WO')).toBeInTheDocument();
});

test('click flows update state and show toasts', () => {
  render(<MaterialsPanel items={items} />);

  const raiseBtn = screen.getByLabelText('Raise RFQ');
  fireEvent.click(raiseBtn);
  expect(screen.getByRole('status')).toHaveTextContent('RFQ raised');
  expect(raiseBtn).toBeDisabled();

  const pickListBtn = screen.getByLabelText('Issue pick list');
  fireEvent.click(pickListBtn);
  expect(screen.getByRole('status')).toHaveTextContent('Pick list issued');
  expect(pickListBtn).toBeDisabled();

  const parkBtn = screen.getByLabelText('Park WO');
  fireEvent.click(parkBtn);
  expect(screen.getByRole('status')).toHaveTextContent('Work order parked');
  expect(screen.queryByLabelText('Park WO')).toBeNull();
  const unparkBtn = screen.getByLabelText('Unpark');
  fireEvent.click(unparkBtn);
  expect(screen.getByRole('status')).toHaveTextContent('Work order unparked');
  expect(screen.getByLabelText('Park WO')).toBeInTheDocument();
});


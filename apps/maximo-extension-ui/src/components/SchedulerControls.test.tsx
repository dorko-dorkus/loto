import { render, screen, fireEvent } from '@testing-library/react';
import { test, expect } from 'vitest';
import SchedulerControls from './SchedulerControls';

test('changing α updates displayed value', () => {
  render(<SchedulerControls />);
  const alphaInput = screen.getByLabelText('α (spot exposure)');
  fireEvent.change(alphaInput, { target: { value: '0.75' } });
  expect(screen.getByTestId('alpha-display')).toHaveTextContent('0.75');
});

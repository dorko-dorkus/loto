import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test } from 'vitest';
import Page from './page';

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  cleanup();
});

test('matches snapshot', () => {
  const { container } = render(<Page />);
  expect(container.firstChild).toMatchSnapshot();
});

test('initializes from and persists to localStorage', async () => {
  window.localStorage.setItem('wizard-step', '1');
  window.localStorage.setItem(
    'wizard-data',
    JSON.stringify({ name: 'Bob', age: '42' })
  );
  render(<Page />);
  const age = screen.getByLabelText('age');
  expect(age).toHaveValue('42');

  fireEvent.change(age, { target: { value: '30' } });
  fireEvent.click(screen.getByText('Next'));

  expect(window.localStorage.getItem('wizard-step')).toBe('2');
  const stored = window.localStorage.getItem('wizard-data');
  expect(stored && JSON.parse(stored)).toEqual({ name: 'Bob', age: '30' });
});


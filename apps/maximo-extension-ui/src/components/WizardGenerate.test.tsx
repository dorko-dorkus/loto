import { render, screen, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import WizardGenerate from './WizardGenerate';
import { apiFetch } from '../lib/api';

vi.mock('../lib/api', () => ({ apiFetch: vi.fn() }));

test('posts data and shows spinner while waiting', async () => {
  localStorage.clear();
  const plan = { plan: 'ok' };
  let resolve: (value: any) => void = () => {};
  (apiFetch as unknown as vi.Mock).mockReturnValue(
    new Promise((res) => {
      resolve = res;
    })
  );

  const setPlan = vi.fn();
  const setStep = vi.fn();

  render(<WizardGenerate data={[]} setPlan={setPlan} setStep={setStep} />);

  expect(screen.getByTestId('wizard-generate-spinner')).toBeInTheDocument();

  resolve({ ok: true, json: () => Promise.resolve(plan) });

  await waitFor(() => expect(setPlan).toHaveBeenCalledWith(plan));
  expect(localStorage.getItem('wizardPlan')).toBe(JSON.stringify(plan));
  expect(setStep).toHaveBeenCalledWith(3);
  expect(screen.queryByTestId('wizard-generate-spinner')).toBeNull();
});


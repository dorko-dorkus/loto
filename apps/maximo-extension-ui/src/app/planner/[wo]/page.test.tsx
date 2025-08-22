import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { test, expect, vi, afterEach } from 'vitest';
import Page from './page';

afterEach(() => {
  vi.restoreAllMocks();
  cleanup();
});

test('renders 6 tabs', async () => {
  render(<Page params={{ wo: 'WO-1' }} />);
  const tabs = await screen.findAllByRole('tab');
  expect(tabs).toHaveLength(6);
});

test('renders export buttons', () => {
  render(<Page params={{ wo: 'WO-1' }} />);
  expect(screen.getAllByText('Export PDF').length).toBeGreaterThan(0);
  expect(screen.getAllByText('Export JSON').length).toBeGreaterThan(0);
});

test('renders material status chips', async () => {
  const shortage = {
    steps: [],
    unavailable_assets: [],
    unit_mw_delta: {},
    blocked_by_parts: true,
    parts_status: { 'P-100': 'ok', 'P-200': 'short' }
  };
  vi.spyOn(global, 'fetch').mockResolvedValue({
    ok: true,
    json: async () => shortage
  } as Response);
  vi.stubEnv('NEXT_PUBLIC_USE_API', 'true');

  render(<Page params={{ wo: 'WO-1' }} />);
  const tab = await screen.findByRole('tab', { name: 'Materials' });
  fireEvent.click(tab);
  await screen.findByText('P-200');
  expect(screen.getByText('OK')).toBeInTheDocument();
  expect(screen.getByText('Short')).toBeInTheDocument();
});

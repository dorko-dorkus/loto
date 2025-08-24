import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { test, expect, vi, afterEach, beforeEach } from 'vitest';
import Page from './page';

beforeEach(() => {
  vi.stubGlobal('alert', vi.fn());
});

afterEach(() => {
  vi.restoreAllMocks();
  cleanup();
  vi.unstubAllGlobals();
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

test('plan tab filters steps and allows copy', async () => {
  render(<Page params={{ wo: 'WO-1' }} />);
  const search = await screen.findByPlaceholderText('Search steps');
  fireEvent.change(search, { target: { value: 'install' } });
  expect(screen.getByText('Install')).toBeInTheDocument();
  expect(screen.queryByText('Remove')).toBeNull();
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

test('commit button gated by policies', async () => {
  vi.stubEnv('NEXT_PUBLIC_ROLE', 'ADMIN');
  render(<Page params={{ wo: 'WO-1' }} />);
  const commitTab = await screen.findByRole('tab', { name: 'Commit' });
  fireEvent.click(commitTab);
  const btn = await screen.findByRole('button', { name: 'Commit' });
  expect(btn).toBeDisabled();
  const checks = screen.getAllByRole('checkbox');
  checks.forEach((c) => fireEvent.click(c));
  expect(btn).not.toBeDisabled();
});

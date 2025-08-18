import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { test, expect, vi, afterEach } from 'vitest';
import Exports from './Exports';
import * as exportPidModule from '../lib/exportPid';

const originalFetch = global.fetch;

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  global.fetch = originalFetch;
});

test('downloads PDF with hash and seed', async () => {
  const hash = 'abc123';
  const seed = '42';
  const blob = new Blob(['pdf'], { type: 'application/pdf' });
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    headers: new Headers({ 'x-loto-hash': hash, 'x-loto-seed': seed }),
    blob: () => Promise.resolve(blob)
  });
  global.fetch = fetchMock as any;

  const click = vi.fn();
  const origCreate = document.createElement.bind(document);
  let anchor: HTMLAnchorElement;
  vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
    if (tag === 'a') {
      anchor = origCreate('a') as HTMLAnchorElement;
      anchor.click = click;
      return anchor;
    }
    return origCreate(tag);
  });
  (global as any).URL.createObjectURL = vi.fn(() => 'blob:mock');
  (global as any).URL.revokeObjectURL = vi.fn();

  render(<Exports wo="1" />);
  fireEvent.click(screen.getByText('Export PDF'));
  await waitFor(() => expect(fetchMock).toHaveBeenCalled());

  expect(anchor.download).toBe('WO-1_abc123.pdf');
  expect(click).toHaveBeenCalled();
  await screen.findByText('Hash: abc123');
  await screen.findByText('Seed: 42');
});

test('downloads JSON with hash in filename', async () => {
  const hash = 'def456';
  const seed = '7';
  const blob = new Blob(['{}'], { type: 'application/json' });
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    headers: new Headers({ 'x-loto-hash': hash, 'x-loto-seed': seed }),
    blob: () => Promise.resolve(blob)
  });
  global.fetch = fetchMock as any;

  const click = vi.fn();
  const origCreate2 = document.createElement.bind(document);
  let anchor2: HTMLAnchorElement;
  vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
    if (tag === 'a') {
      anchor2 = origCreate2('a') as HTMLAnchorElement;
      anchor2.click = click;
      return anchor2;
    }
    return origCreate2(tag);
  });
  (global as any).URL.createObjectURL = vi.fn(() => 'blob:mock');
  (global as any).URL.revokeObjectURL = vi.fn();

  render(<Exports wo="2" />);
  fireEvent.click(screen.getByText('Export JSON'));
  await waitFor(() => expect(fetchMock).toHaveBeenCalled());

  expect(anchor2.download).toBe('WO-2_def456.json');
  expect(click).toHaveBeenCalled();
  await screen.findByText('Hash: def456');
  await screen.findByText('Seed: 7');
});

test('exports P&ID view as PDF', async () => {
  const spy = vi.spyOn(exportPidModule, 'exportPid').mockResolvedValue();
  const div = document.createElement('div');
  div.id = 'pid-container';
  document.body.appendChild(div);

  render(<Exports wo="3" />);
  fireEvent.click(screen.getByText('Export P&ID'));
  await waitFor(() => expect(spy).toHaveBeenCalledWith('WO-3_pid.pdf'));

  document.body.removeChild(div);
});

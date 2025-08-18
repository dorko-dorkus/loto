import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import Exports from './Exports';

afterEach(() => {
  vi.restoreAllMocks();
  cleanup();
});

test('export buttons download files and display hash', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(
      new Response('pdfdata', {
        headers: { 'content-type': 'application/pdf', 'x-hash': 'hashpdf' }
      })
    )
    .mockResolvedValueOnce(
      new Response('jsondata', {
        headers: { 'content-type': 'application/json', 'x-hash': 'hashjson' }
      })
    );
  // @ts-ignore
  global.fetch = fetchMock;

  (global.URL as any).createObjectURL = vi.fn(() => 'blob:url');
  (global.URL as any).revokeObjectURL = vi.fn();

  const anchors: HTMLAnchorElement[] = [];
  const origCreate = document.createElement.bind(document);
  vi.spyOn(document, 'createElement').mockImplementation((tag: any) => {
    const el = origCreate(tag);
    if (tag === 'a') anchors.push(el as HTMLAnchorElement);
    return el;
  });
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

  render(<Exports wo="WO1" />);

  fireEvent.click(screen.getByText('Export PDF'));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  expect(anchors[0].download).toBe('WO1-hashpdf.pdf');
  expect(screen.getByRole('status')).toHaveTextContent('hashpdf');

  fireEvent.click(screen.getByText('Export JSON'));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect(anchors[1].download).toBe('WO1-hashjson.json');
  expect(screen.getByRole('status')).toHaveTextContent('hashjson');
});


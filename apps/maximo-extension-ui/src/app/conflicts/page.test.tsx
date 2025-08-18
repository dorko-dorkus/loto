import { render, fireEvent, screen, waitFor, cleanup } from '@testing-library/react';
import { test, expect, vi, afterEach } from 'vitest';
import Page from './page';

const candidates = [
  { id: 1, deltaTime: '+1d', deltaCost: '+$100', readiness: 'High', isolation: true },
  { id: 2, deltaTime: '-2d', deltaCost: '-$50', readiness: 'Medium', isolation: false }
];

function setupFetchMock() {
  return vi.fn((url: RequestInfo) => {
    if (typeof url === 'string' && url.startsWith('/bundling?')) {
      return Promise.resolve({ json: () => Promise.resolve(candidates) });
    }
    if (typeof url === 'string' && url === '/bundling/recommend') {
      return Promise.resolve({ json: () => Promise.resolve([1]) });
    }
    return Promise.reject(new Error(`Unhandled fetch: ${url}`));
  }) as any;
}

afterEach(() => cleanup());

test('renders candidate table and toggles selection', async () => {
  global.fetch = setupFetchMock();
  render(<Page />);
  const checkboxes = (await screen.findAllByRole('checkbox')) as HTMLInputElement[];
  expect(checkboxes.length).toBeGreaterThan(0);
  const first = checkboxes[0];
  expect(first.checked).toBe(false);
  fireEvent.click(first);
  expect(first.checked).toBe(true);
});

test('recommends via API and shows toast', async () => {
  global.fetch = setupFetchMock();
  render(<Page />);
  const checkboxes = await screen.findAllByRole('checkbox');
  fireEvent.click(checkboxes[0]);
  fireEvent.click(screen.getByText('Recommend'));
  await waitFor(() =>
    expect(screen.getByRole('status')).toHaveTextContent('Recommended: 1')
  );
});

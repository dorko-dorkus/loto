import { render, waitFor } from '@testing-library/react';
import { vi, test, expect } from 'vitest';
import PidViewer from './PidViewer';

test('toggles highlight classes', async () => {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>';
  vi.spyOn(global, 'fetch').mockResolvedValue({
    text: () => Promise.resolve(svg)
  } as any);

  const { container, rerender } = render(
    <PidViewer src="/test.svg" highlight="primary" />
  );

  await waitFor(() => {
    const svgEl = container.querySelector('svg');
    expect(svgEl).toBeTruthy();
    expect(svgEl!.classList.contains('hl-primary')).toBe(true);
  });

  rerender(<PidViewer src="/test.svg" highlight="warning" />);
  await waitFor(() => {
    const svgEl = container.querySelector('svg');
    expect(svgEl!.classList.contains('hl-warning')).toBe(true);
  });

  (fetch as any).mockRestore();
});

test('adds aria-labels from title elements', async () => {
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="5" height="5"><title>Valve 1</title></rect></svg>';
  vi.spyOn(global, 'fetch').mockResolvedValue({
    text: () => Promise.resolve(svg)
  } as any);

  const { container } = render(<PidViewer src="/test.svg" />);

  await waitFor(() => {
    const rect = container.querySelector('rect');
    expect(rect?.getAttribute('aria-label')).toBe('Valve 1');
    expect(rect?.getAttribute('tabindex')).toBe('0');
  });

  (fetch as any).mockRestore();
});

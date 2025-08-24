import { render, waitFor, fireEvent, cleanup } from '@testing-library/react';
import { vi, test, expect, afterEach } from 'vitest';
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

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

test('renders warning messages and copies on click', async () => {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>';
  vi.spyOn(global, 'fetch').mockResolvedValue({
    text: () => Promise.resolve(svg)
  } as any);

  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.assign(navigator, { clipboard: { writeText } });

  const { getByRole, findByRole, getAllByRole } = render(
    <PidViewer src="/test.svg" warnings={['missing tag']} />
  );

  const btn = await waitFor(() => getByRole('button', { name: /warnings/i }));
  // legend uses an explicit landmark role
  expect(getAllByRole('note', { name: 'Legend' }).length).toBeGreaterThan(0);
  fireEvent.click(btn);
  const warnBtn = await findByRole('button', { name: 'missing tag' });
  // warnings drawer is labeled for accessibility
  await findByRole('complementary', { name: 'Warnings' });
  fireEvent.click(warnBtn);
  expect(writeText).toHaveBeenCalledWith('missing tag');

  (fetch as any).mockRestore();
});

test('supports pan and zoom interactions', async () => {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"></svg>';
  vi.spyOn(global, 'fetch').mockResolvedValue({
    text: () => Promise.resolve(svg)
  } as any);

  const { container } = render(<PidViewer src="/test.svg" />);
  const wrapper = container.querySelector('.pid-container') as HTMLDivElement;
  Object.defineProperty(wrapper, 'clientWidth', { value: 100 });
  Object.defineProperty(wrapper, 'clientHeight', { value: 100 });
  wrapper.getBoundingClientRect = () => ({
    left: 0,
    top: 0,
    width: 100,
    height: 100,
    right: 100,
    bottom: 100,
    x: 0,
    y: 0,
    toJSON() {
      return {};
    }
  });

  await waitFor(() => expect(container.querySelector('svg')).toBeTruthy());
  const svgEl = container.querySelector('svg') as SVGSVGElement;

  fireEvent.wheel(wrapper, { deltaY: -100, clientX: 50, clientY: 50 });
  await waitFor(() => {
    expect(svgEl.style.transform).toMatch(/scale/);
  });
  const afterZoom = svgEl.style.transform;

  fireEvent.mouseDown(wrapper, { clientX: 0, clientY: 0 });
  fireEvent.mouseMove(wrapper, { clientX: 10, clientY: 20 });
  fireEvent.mouseUp(wrapper);

  await waitFor(() => {
    expect(svgEl.style.transform).not.toBe(afterZoom);
  });

  (fetch as any).mockRestore();
});

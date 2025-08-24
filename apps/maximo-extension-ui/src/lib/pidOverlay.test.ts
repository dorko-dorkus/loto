import { describe, it, expect } from 'vitest';
import { applyPidOverlay, type Overlay } from './pidOverlay';

function createSvg(ids: string[]): SVGSVGElement {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  ids.forEach((id) => {
    const el = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    el.setAttribute('id', id);
    svg.appendChild(el);
  });
  return svg;
}

describe('applyPidOverlay', () => {
  it('highlights elements and adds badges', () => {
    const svg = createSvg(['a', 'b']);
    const overlay: Overlay = {
      highlight: ['#a', '#b'],
      badges: [
        { selector: '#a', type: 'asset' },
        { selector: '#b', type: 'source' }
      ],
      paths: []
    };

    applyPidOverlay(svg, overlay);

    const a = svg.querySelector('#a')!;
    const b = svg.querySelector('#b')!;
    expect(a.classList.contains('hl-primary')).toBe(true);
    expect(b.classList.contains('hl-primary')).toBe(true);

    const badges = Array.from(svg.querySelectorAll('.pid-badge'));
    expect(badges).toHaveLength(2);
    expect(badges[0].textContent).toBe('asset');
    expect(badges[0].classList.contains('pid-badge-asset')).toBe(true);
    expect(badges[1].textContent).toBe('source');
    expect(badges[1].classList.contains('pid-badge-source')).toBe(true);
  });

  it('returns unique warnings', () => {
    const svg = createSvg([]);
    const overlay: Overlay = {
      highlight: [],
      badges: [],
      paths: [],
      warnings: ['missing tag', 'missing tag', 'unmapped'],
    };

    const warnings = applyPidOverlay(svg, overlay);
    expect(warnings).toEqual(['missing tag', 'unmapped']);
  });

  it('handles viewBox transforms and nested groups', () => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100 50');
    const outer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    outer.setAttribute('transform', 'translate(10 5)');
    const inner = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    inner.setAttribute('transform', 'scale(2)');
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('id', 'target');
    rect.setAttribute('x', '5');
    rect.setAttribute('y', '5');
    rect.setAttribute('width', '20');
    rect.setAttribute('height', '10');
    inner.appendChild(rect);
    outer.appendChild(inner);
    svg.appendChild(outer);

    const overlay: Overlay = {
      highlight: ['#target'],
      badges: [{ selector: '#target', type: 'asset' }],
      paths: [],
    };

    applyPidOverlay(svg as unknown as SVGSVGElement, overlay);
    expect(svg.querySelector('.pid-badge')).toBeTruthy();
  });
});

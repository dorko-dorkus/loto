export interface Badge {
  selector: string;
  type: string;
}

export interface OverlayPath {
  id: string;
  selectors: string[];
}

export interface Overlay {
  highlight: string[];
  badges: Badge[];
  paths: OverlayPath[];
}

/**
 * Apply overlay information to an SVG diagram.
 *
 * Elements matching selectors in `highlight` receive the `hl-primary` class.
 * Badges are rendered near their target elements using SVG `foreignObject`
 * elements so that HTML can be positioned relative to the graphic.
 */
export function applyPidOverlay(svg: SVGSVGElement, overlay: Overlay): void {
  overlay.highlight.forEach((selector) => {
    svg.querySelectorAll<SVGElement>(selector).forEach((el) => {
      el.classList.add('hl-primary');
    });
  });

  const badgeLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  badgeLayer.setAttribute('data-badge-layer', '');
  svg.appendChild(badgeLayer);

  overlay.badges.forEach((badge) => {
    const target = svg.querySelector<SVGGraphicsElement>(badge.selector);
    if (!target) return;

    let bbox: DOMRect | { x: number; y: number; width: number; height: number };
    try {
      bbox = target.getBBox();
    } catch {
      bbox = { x: 0, y: 0, width: 0, height: 0 };
    }

    const fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
    fo.setAttribute('x', String(bbox.x));
    fo.setAttribute('y', String(bbox.y));
    fo.setAttribute('width', String(bbox.width));
    fo.setAttribute('height', String(bbox.height));

    const div = document.createElement('div');
    div.className = 'pid-badge';
    div.textContent = badge.type;
    fo.appendChild(div);

    badgeLayer.appendChild(fo);
  });
}

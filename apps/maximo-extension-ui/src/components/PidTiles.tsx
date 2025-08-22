import React, { useEffect, useRef, useState } from 'react';
import '../styles/pid.css';
import { toastError } from '../lib/toast';

type Highlight = 'primary' | 'warning' | null;

interface PidTilesProps {
  src: string;
  highlight?: Highlight;
}

interface ElementEntry {
  el: SVGGraphicsElement;
  bbox: DOMRect;
}

const DEBOUNCE_MS = 50;

export default function PidTiles({ src, highlight = null }: PidTilesProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<SVGSVGElement>(null);
  const hiddenRef = useRef<HTMLDivElement>(null);
  const elementsRef = useRef<ElementEntry[]>([]);
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const debounceTimer = useRef<number>();

  useEffect(() => {
    async function load() {
      try {
        const r = await fetch(src);
        if ('ok' in r && !r.ok) throw new Error('Failed to load PID');
        const txt = await r.text();
        const div = hiddenRef.current;
        if (!div) return;
        div.innerHTML = txt;
        const svg = div.querySelector('svg');
        if (!svg) return;
        const entries: ElementEntry[] = [];
        const graphics = Array.from(svg.querySelectorAll<SVGGraphicsElement>('*'));
        graphics.forEach((g) => {
          try {
            const bbox = g.getBBox();
            entries.push({ el: g, bbox });
          } catch {
            /* ignore non-graphical elements */
          }
        });
        elementsRef.current = entries;
        div.innerHTML = '';
        fitToScreen(svg);
      } catch (err) {
        toastError('Failed to load PID');
      }
    }
    load();
  }, [src]);

  useEffect(() => {
    scheduleUpdate();
  }, [scale, translate, highlight]);

  function scheduleUpdate() {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = window.setTimeout(updateTiles, DEBOUNCE_MS);
  }

  function updateTiles() {
    const container = containerRef.current;
    const viewport = viewportRef.current;
    if (!container || !viewport) return;
    const viewX = -translate.x / scale;
    const viewY = -translate.y / scale;
    const viewW = container.clientWidth / scale;
    const viewH = container.clientHeight / scale;
    viewport.setAttribute('viewBox', `${viewX} ${viewY} ${viewW} ${viewH}`);
    while (viewport.firstChild) {
      viewport.removeChild(viewport.firstChild);
    }
    const right = viewX + viewW;
    const bottom = viewY + viewH;
    for (const { el, bbox } of elementsRef.current) {
      if (bbox.x > right || bbox.y > bottom || bbox.x + bbox.width < viewX || bbox.y + bbox.height < viewY) {
        continue;
      }
      const clone = el.cloneNode(true) as SVGGraphicsElement;
      applyHighlight(clone);
      viewport.appendChild(clone);
    }
  }

  function applyHighlight(node: SVGElement) {
    node.classList.remove('hl-primary', 'hl-warning');
    if (highlight === 'primary') node.classList.add('hl-primary');
    if (highlight === 'warning') node.classList.add('hl-warning');
  }

  function fitToScreen(svg: SVGSVGElement) {
    const container = containerRef.current;
    if (!container) return;
    const vb = svg.getAttribute('viewBox');
    if (!vb) return;
    const [x, y, w, h] = vb.split(' ').map(Number);
    const scaleX = container.clientWidth / w;
    const scaleY = container.clientHeight / h;
    const s = Math.min(scaleX, scaleY);
    setScale(s);
    setTranslate({
      x: -x * s + (container.clientWidth - w * s) / 2,
      y: -y * s + (container.clientHeight - h * s) / 2
    });
  }

  function handleWheel(e: React.WheelEvent) {
    e.preventDefault();
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;
    const delta = -e.deltaY;
    const zoomFactor = delta > 0 ? 1.1 : 0.9;
    const newScale = Math.min(Math.max(scale * zoomFactor, 0.1), 10);
    const scaleRatio = newScale / scale;
    setScale(newScale);
    setTranslate({
      x: offsetX - scaleRatio * (offsetX - translate.x),
      y: offsetY - scaleRatio * (offsetY - translate.y)
    });
  }

  function startDrag(e: React.MouseEvent) {
    dragging.current = true;
    dragStart.current = { x: e.clientX - translate.x, y: e.clientY - translate.y };
  }

  function onDrag(e: React.MouseEvent) {
    if (!dragging.current) return;
    setTranslate({ x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y });
  }

  function endDrag() {
    dragging.current = false;
  }

  return (
    <div
      ref={containerRef}
      className="pid-container relative w-full h-full overflow-hidden"
      onWheel={handleWheel}
      onMouseDown={startDrag}
      onMouseMove={onDrag}
      onMouseUp={endDrag}
      onMouseLeave={endDrag}
    >
      <svg ref={viewportRef} className="w-full h-full" />
      <div ref={hiddenRef} style={{ display: 'none' }} />
    </div>
  );
}


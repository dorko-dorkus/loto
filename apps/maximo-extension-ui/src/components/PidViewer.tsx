import React, { useEffect, useRef, useState } from 'react';
import '../styles/pid.css';

type Highlight = 'primary' | 'warning' | null;

interface OverlayPath {
  id: string;
  selectors: string[];
}

interface Overlay {
  highlight?: string[];
  badges?: unknown[];
  paths?: OverlayPath[];
}

interface PidViewerProps {
  src: string;
  highlight?: Highlight;
  overlay?: Overlay;
}

export default function PidViewer({ src, highlight = null, overlay }: PidViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgContainerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const highlighted = useRef<SVGElement[]>([]);

  useEffect(() => {
    fetch(src)
      .then((r) => r.text())
      .then((txt) => {
        if (svgContainerRef.current) {
          svgContainerRef.current.innerHTML = txt;
          svgRef.current = svgContainerRef.current.querySelector('svg');
          applyHighlight();
          applyOverlay();
          fitToScreen();
        }
      });
  }, [src]);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    svg.style.transform = `translate(${translate.x}px, ${translate.y}px) scale(${scale})`;
    svg.style.transformOrigin = '0 0';
  }, [scale, translate]);

  useEffect(() => {
    applyHighlight();
  }, [highlight]);

  useEffect(() => {
    applyOverlay();
  }, [overlay]);

  function applyHighlight() {
    const svg = svgRef.current;
    if (!svg) return;
    svg.classList.remove('hl-primary', 'hl-warning');
    if (highlight === 'primary') svg.classList.add('hl-primary');
    if (highlight === 'warning') svg.classList.add('hl-warning');
  }

  function applyOverlay() {
    const svg = svgRef.current;
    if (!svg) return;
    highlighted.current.forEach((el) => {
      el.classList.remove('hl-primary', 'hl-warning');
    });
    highlighted.current = [];
    if (!overlay) return;
    overlay.highlight?.forEach((sel) => {
      svg.querySelectorAll<SVGElement>(sel).forEach((el) => {
        el.classList.add('hl-warning');
        highlighted.current.push(el);
      });
    });
    overlay.paths?.forEach((p) => {
      p.selectors.forEach((sel) => {
        svg.querySelectorAll<SVGElement>(sel).forEach((el) => {
          el.classList.add('hl-primary');
          highlighted.current.push(el);
        });
      });
    });
  }

  function fitToScreen() {
    const container = containerRef.current;
    const svg = svgRef.current;
    if (!container || !svg) return;
    const vb = svg.getAttribute('viewBox');
    if (!vb) return;
    const [x, y, w, h] = vb.split(' ').map(Number);
    const scaleX = container.clientWidth / w;
    const scaleY = container.clientHeight / h;
    const s = Math.min(scaleX, scaleY);
    setScale(s);
    setTranslate({
      x: -x * s + (container.clientWidth - w * s) / 2,
      y: -y * s + (container.clientHeight - h * s) / 2,
    });
  }

  function resetView() {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
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
      y: offsetY - scaleRatio * (offsetY - translate.y),
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

  function handleKey(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === '+' || e.key === '=') {
      setScale((s) => Math.min(s * 1.1, 10));
    } else if (e.key === '-') {
      setScale((s) => Math.max(s * 0.9, 0.1));
    }
  }

  return (
    <div
      className="pid-container relative w-full h-full"
      tabIndex={0}
      ref={containerRef}
      onWheel={handleWheel}
      onKeyDown={handleKey}
      onMouseDown={startDrag}
      onMouseMove={onDrag}
      onMouseUp={endDrag}
      onMouseLeave={endDrag}
    >
      <div ref={svgContainerRef} className="w-full h-full" />
      <div className="controls absolute top-2 left-2 flex gap-2">
        <button className="badge" onClick={fitToScreen} type="button">
          Fit
        </button>
        <button className="badge" onClick={resetView} type="button">
          Reset
        </button>
      </div>
    </div>
  );
}


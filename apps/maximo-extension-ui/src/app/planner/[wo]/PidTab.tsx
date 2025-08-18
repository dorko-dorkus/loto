'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import PidViewer from '../../../components/PidViewer';
import { applyPidOverlay, type Overlay } from '../../../lib/pidOverlay';

interface OverlayResponse extends Overlay {
  drawingId: string;
}

async function fetchOverlay(wo: string): Promise<OverlayResponse> {
  const res = await fetch(`/pid/overlay?wo=${wo}`);
  if (!res.ok) {
    throw new Error('Failed to fetch overlay');
  }
  return res.json();
}

export default function PidTab({ wo }: { wo: string }) {
  const { data } = useQuery({ queryKey: ['pid', wo], queryFn: () => fetchOverlay(wo) });
  const [showSimFails, setShowSimFails] = useState(false);
  const [showSourcePath, setShowSourcePath] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!data || !containerRef.current) return;
    const svg = containerRef.current.querySelector('svg');
    if (!svg) return;

    svg.querySelectorAll('.hl-primary').forEach((el) => el.classList.remove('hl-primary'));
    svg.querySelectorAll('[data-badge-layer]').forEach((el) => el.remove());

    const highlight = [...data.highlight];
    const sourcePath = data.paths[0]?.selectors ?? [];
    const simFailSelectors = data.paths.slice(1).flatMap((p) => p.selectors);
    if (showSourcePath) highlight.push(...sourcePath);
    if (showSimFails) highlight.push(...simFailSelectors);

    applyPidOverlay(svg as unknown as SVGSVGElement, {
      highlight,
      badges: data.badges,
      paths: []
    });
  }, [data, showSimFails, showSourcePath]);

  if (!data) return null;

  const src = `/pid/${data.drawingId}/svg`;

  return (
    <div className="flex h-full flex-col">
      <div className="mb-2 flex gap-4">
        <label>
          <input
            type="checkbox"
            checked={showSimFails}
            onChange={(e) => setShowSimFails(e.target.checked)}
          />
          {' '}Show sim fails
        </label>
        <label>
          <input
            type="checkbox"
            checked={showSourcePath}
            onChange={(e) => setShowSourcePath(e.target.checked)}
          />
          {' '}Show sources→asset path
        </label>
      </div>
      <div ref={containerRef} className="flex-1">
        <PidViewer src={src} />
      </div>
    </div>
  );
}


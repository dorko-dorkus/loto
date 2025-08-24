'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import yaml from 'js-yaml';
import { useBlueprintApi } from '../../../lib/hooks';
import PidViewer from '../../../components/PidViewer';
import Skeleton from '../../../components/Skeleton';
import { applyPidOverlay, type Overlay } from '../../../lib/pidOverlay';
import { apiFetch } from '../../../lib/api';
import type { BlueprintData } from '../../../types/api';
import { toastError } from '../../../lib/toast';

interface OverlayResponse extends Overlay {
  drawingId: string;
}

async function fetchOverlay(wo: string, blueprint: BlueprintData): Promise<OverlayResponse> {
  const mapRes = await fetch('/demo/pids/pid_map.yaml');
  if ('ok' in mapRes && !mapRes.ok) {
    throw new Error('Failed to fetch pid map');
  }
  const pidMap = yaml.load(await mapRes.text()) as Record<string, unknown>;

  const plan = {
    plan_id: wo,
    actions: blueprint.steps.map((s) => ({ component_id: s.component_id, method: s.method })),
    verifications: []
  };

  const res = await apiFetch('/pid/overlay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sources: ['src'],
      asset: 'A-100',
      plan,
      sim_fail_paths: [],
      pid_map: pidMap
    })
  });
  if ('ok' in res && !res.ok) {
    throw new Error('Failed to fetch overlay');
  }
  const overlay = await res.json();
  return { ...overlay, drawingId: 'demo' };
}

export default function PidTab({ wo }: { wo: string }) {
  const { data: blueprint, isLoading: blueprintLoading } = useBlueprintApi(wo);
  const { data, isLoading } = useQuery({
    queryKey: ['pid', wo],
    enabled: !!blueprint,
    queryFn: async () => {
      try {
        return await fetchOverlay(wo, blueprint as BlueprintData);
      } catch (err) {
        toastError('Failed to fetch PID overlay');
        throw err;
      }
    }
  });
  const [showSimFails, setShowSimFails] = useState(false);
  const [showSourcePath, setShowSourcePath] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

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

    const w = applyPidOverlay(svg as unknown as SVGSVGElement, {
      highlight,
      badges: data.badges,
      paths: [],
      warnings: data.warnings
    });
    setWarnings(w);
  }, [data, showSimFails, showSourcePath]);

  if (blueprintLoading || isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }
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
        <PidViewer src={src} warnings={warnings} />
      </div>
    </div>
  );
}


'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import PidViewer from '../../../components/PidViewer';
import { useBlueprint } from '../../../lib/hooks';
import type { BlueprintStep } from '../../../types/api';

interface OverlayResponse {
  highlight: string[];
  badges: unknown[];
  paths: unknown[];
}

async function fetchOverlay(
  wo: string,
  showSimFails: boolean,
  showPath: boolean,
  plan: BlueprintStep[] | undefined,
): Promise<OverlayResponse> {
  const payload = {
    sources: showPath ? [] : [],
    asset: 'A',
    plan: {
      plan_id: wo,
      actions: Array.isArray(plan)
        ? plan.map((p) => ({ component_id: p.component_id, method: p.method }))
        : [],
      verifications: [],
    },
    sim_fail_paths: showSimFails ? [] : [],
    pid_map: {},
  };
  const res = await fetch('/pid/overlay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error('Failed to fetch overlay');
  }
  return res.json();
}

export default function PidTab({ wo }: { wo: string }) {
  const [showSimFails, setShowSimFails] = useState(false);
  const [showPath, setShowPath] = useState(false);

  const { data: blueprint } = useBlueprint(wo);

  const { data: overlay } = useQuery({
    queryKey: ['pidOverlay', wo, showSimFails, showPath],
    enabled: !!blueprint,
    queryFn: () => fetchOverlay(wo, showSimFails, showPath, blueprint?.steps),
  });

  return (
    <div className="h-full flex flex-col">
      <div className="mb-2 space-x-4">
        <label className="mr-4">
          <input
            type="checkbox"
            checked={showSimFails}
            onChange={(e) => setShowSimFails(e.target.checked)}
          />{' '}
          Show sim fails
        </label>
        <label>
          <input
            type="checkbox"
            checked={showPath}
            onChange={(e) => setShowPath(e.target.checked)}
          />{' '}
          Show sources→asset path
        </label>
      </div>
      <div className="flex-1 border border-[var(--mxc-border)]">
        <PidViewer src={`/pid/${wo}/svg`} overlay={overlay} />
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useBlueprintApi } from '../../../lib/hooks';
import Button from '../../../components/Button';
import { toastError } from '../../../lib/toast';

interface CommitPanelProps {
  wo: string;
  simOk: boolean;
}

export default function CommitPanel({ wo, simOk }: CommitPanelProps) {
  const { data } = useBlueprintApi(wo);
  const role = (process.env.NEXT_PUBLIC_ROLE || 'TEST').toUpperCase();
  const canCommit = role !== 'TEST';
  const diff = data?.diff;
  const audit = data?.audit_metadata as Record<string, unknown> | undefined;
  const [policies, setPolicies] = useState({ safe: false, log: false });
  const policiesAccepted = Object.values(policies).every(Boolean);

  const handleCommit = async () => {
    const input = window.prompt('Type COMMIT to confirm');
    if (input !== 'COMMIT') return;
    try {
      const res = await fetch(`/api/commit/${wo}`, { method: 'POST' });
      if ('ok' in res && !res.ok) throw new Error('Failed to commit');
    } catch (err) {
      toastError('Failed to commit');
    }
  };

  return (
    <section>
      {diff && (
        <pre className="mb-4 overflow-x-auto border p-2 text-sm" data-testid="diff">
          {diff}
        </pre>
      )}
      {audit && (
        <div className="mb-4">
          <h2 className="mb-1 font-semibold">Audit Metadata</h2>
          <pre className="overflow-x-auto border p-2 text-sm">
            {JSON.stringify(audit, null, 2)}
          </pre>
        </div>
      )}
      <div className="mb-4 space-y-2">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={policies.safe}
            onChange={(e) =>
              setPolicies((p) => ({ ...p, safe: e.target.checked }))
            }
          />
          Follow safety policy
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={policies.log}
            onChange={(e) =>
              setPolicies((p) => ({ ...p, log: e.target.checked }))
            }
          />
          Review log
        </label>
      </div>
      <Button
        disabled={!canCommit || !simOk || !policiesAccepted}
        onClick={handleCommit}
      >
        Commit
      </Button>
    </section>
  );
}


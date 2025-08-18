'use client';

import { useBlueprint } from '../../../lib/hooks';
import Button from '../../../components/Button';

interface CommitPanelProps {
  wo: string;
}

export default function CommitPanel({ wo }: CommitPanelProps) {
  const { data } = useBlueprint(wo);
  const role = (process.env.NEXT_PUBLIC_ROLE || 'TEST').toUpperCase();
  const canCommit = role !== 'TEST';
  const diff = data?.diff;
  const audit = data?.audit_metadata as Record<string, unknown> | undefined;

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
      <Button disabled={!canCommit}>Commit</Button>
    </section>
  );
}


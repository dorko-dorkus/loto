
'use client';

import { useEffect, useState } from 'react';
import { SimulationResult } from '../../types/api';

// Fetch candidate bundling options for a work order
async function fetchCandidates(): Promise<SimulationResult[]> {
  const res = await fetch('/bundling?wo=1');
  return res.json();
}

export default function ConflictsPage() {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [candidates, setCandidates] = useState<SimulationResult[]>([]);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    fetchCandidates().then(setCandidates);
  }, []);

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <main>
      <h1 className="mb-4 text-xl font-semibold">Conflicts & Bundling</h1>
      <table className="w-full border border-[var(--mxc-border)]">
        <thead className="bg-[var(--mxc-nav-bg)] text-left">
          <tr>
            <th className="px-4 py-2"></th>
            <th className="px-4 py-2">ΔTime</th>
            <th className="px-4 py-2">ΔCost</th>
            <th className="px-4 py-2">Readiness</th>
            <th className="px-4 py-2">Isolation subset?</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c) => (
            <tr key={c.id}>
              <td className="px-4 py-2">
                <input
                  type="checkbox"
                  checked={selected.has(c.id)}
                  onChange={() => toggle(c.id)}
                  aria-label={`Select candidate ${c.id}`}
                />
              </td>
              <td className="px-4 py-2">{c.deltaTime}</td>
              <td className="px-4 py-2">{c.deltaCost}</td>
              <td className="px-4 py-2">{c.readiness}</td>
              <td className="px-4 py-2">{c.isolation ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button
        className="mt-4 rounded border border-[var(--mxc-border)] px-4 py-2"
        onClick={async () => {
          const res = await fetch('/bundling/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selected: Array.from(selected) })
          });
          const ids: number[] = await res.json();
          setSelected(new Set(ids));
          setToast(`Recommended: ${ids.join(', ')}`);
          console.log('Recommend', ids);
        }}
      >
        Recommend
      </button>
      {toast && (
        <div role="status" aria-live="polite" className="mt-2 text-sm">
          {toast}
        </div>
      )}
    </main>
  );
}


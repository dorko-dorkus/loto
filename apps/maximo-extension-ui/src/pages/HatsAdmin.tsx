import { useMemo, useState } from 'react';
import { useHats } from '../lib/hats';
import type { HatSnapshot } from '../types/api';

function Sparkline({ value }: { value: number }) {
  const h = 20;
  const w = 60;
  const y = h - value * h;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="text-[var(--mxc-topbar-bg)]">
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="1"
        points={`0,${y} ${w},${y}`}
      />
    </svg>
  );
}

export default function HatsAdmin() {
  const { data } = useHats();
  const hats: HatSnapshot[] = data ?? [];

  const [weights, setWeights] = useState<Record<string, number>>({});
  const [locked, setLocked] = useState<Record<string, boolean>>({});
  const [showInfo, setShowInfo] = useState(false);

  const weighted = useMemo(() => {
    return hats
      .map((h) => {
        const weight = weights[h.hat_id] ?? 1;
        return { ...h, weight, preview: h.c_r * weight };
      })
      .sort((a, b) => b.preview - a.preview);
  }, [hats, weights]);

  const updateWeight = (id: string, v: number) => {
    setWeights((prev) => ({ ...prev, [id]: v }));
  };

  const toggleLock = (id: string) => {
    setLocked((prev) => ({ ...prev, [id]: !(prev[id] ?? true) }));
  };

  return (
    <main>
      <h1 className="mb-4 text-xl font-semibold">Hats Admin</h1>
      <div className="mb-4 text-sm">
        <button
          className="underline"
          type="button"
          onClick={() => setShowInfo(!showInfo)}
        >
          explain rank
        </button>
        {showInfo && (
          <div className="mt-2 max-w-md rounded border bg-white p-2 shadow">
            Rankings use an exponentially weighted moving average (EWMA)
            with shrinkage toward neutral performance.
          </div>
        )}
      </div>
      <table className="min-w-full border border-[var(--mxc-border)]">
        <thead className="bg-[var(--mxc-nav-bg)] text-left">
          <tr>
            <th className="px-4 py-2">Hat</th>
            <th className="px-4 py-2">Rank</th>
            <th className="px-4 py-2">c_r</th>
            <th className="px-4 py-2">Samples</th>
            <th className="px-4 py-2">Last event</th>
            <th className="px-4 py-2">Trend</th>
            <th className="px-4 py-2">Weight</th>
          </tr>
        </thead>
        <tbody>
          {weighted.map((h) => (
            <tr key={h.hat_id}>
              <td className="px-4 py-2">{h.hat_id}</td>
              <td className="px-4 py-2">{h.rank}</td>
              <td className="px-4 py-2">{h.c_r.toFixed(2)}</td>
              <td className="px-4 py-2">{h.n_samples}</td>
              <td className="px-4 py-2">
                {h.last_event_at ? new Date(h.last_event_at).toLocaleString() : '-'}
              </td>
              <td className="px-4 py-2">
                <Sparkline value={h.c_r} />
              </td>
              <td className="px-4 py-2">
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min={0}
                    max={2}
                    step={0.1}
                    value={weights[h.hat_id] ?? 1}
                    disabled={locked[h.hat_id] ?? true}
                    onChange={(e) => updateWeight(h.hat_id, Number(e.target.value))}
                  />
                  <button
                    type="button"
                    className="text-xl"
                    onClick={() => toggleLock(h.hat_id)}
                  >
                    {locked[h.hat_id] ?? true ? '🔒' : '🔓'}
                  </button>
                </div>
              </td>
            </tr>
          ))}
          {weighted.length === 0 && (
            <tr>
              <td className="px-4 py-6 text-center" colSpan={7}>
                No data
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </main>
  );
}

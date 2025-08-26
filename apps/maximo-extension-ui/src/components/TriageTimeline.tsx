import React from 'react';

export interface TriageLane {
  id: string;
  rank: 1 | 2 | 3 | 4;
  cr: number;
  c: number;
  r: number;
  kpis: Array<number | string>;
}

/**
 * Render a simple triage timeline with rank badges and accessible tooltips.
 */
export default function TriageTimeline({ lanes }: { lanes: TriageLane[] }) {
  return (
    <div className="flex flex-col space-y-2">
      {lanes.map((lane) => {
        const tooltip = `cr ${lane.cr}\nc ${lane.c}\nr ${lane.r}\n${lane.kpis.slice(-3).join(', ')}`;
        return (
          <div key={lane.id} className="relative h-6 flex items-center pl-8">
            <span
              className="absolute left-0 inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-500 text-white text-xs font-bold"
            >
              {lane.rank}
            </span>
            <div
              role="tooltip"
              aria-label={tooltip}
              className="flex-1 h-4 bg-gray-200 rounded"
              title={tooltip}
            />
          </div>
        );
      })}
    </div>
  );
}

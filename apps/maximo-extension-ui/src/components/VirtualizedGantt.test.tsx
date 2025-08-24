import { fireEvent, render, screen } from '@testing-library/react';
import React, { useState } from 'react';
import { expect, test } from 'vitest';
import VirtualizedGantt from './VirtualizedGantt';
import ConflictsList from './ConflictsList';
import type { SchedulePoint } from '../lib/schedule';

class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
// @ts-ignore
global.ResizeObserver = ResizeObserver;

const data: SchedulePoint[] = [
  {
    date: '2024-01-01',
    p10: 1,
    p50: 2,
    p90: 3,
    price: 4,
    hats: 1,
    conflicts: ['A']
  },
  {
    date: '2024-01-02',
    p10: 1,
    p50: 2,
    p90: 3,
    price: 4,
    hats: 1,
    conflicts: []
  }
];

function Wrapper() {
  const [conflicts, setConflicts] = useState<string[]>([]);
  return (
    <>
      <VirtualizedGantt
        data={data}
        onSelect={(p) => setConflicts(p.conflicts ?? [])}
      />
      <ConflictsList
        candidates={conflicts.map((c, i) => ({
          id: `c${i}`,
          label: c,
          explanation: c
        }))}
      />
    </>
  );
}

test('conflicts list updates on row selection', async () => {
  render(<Wrapper />);
  const firstRow = await screen.findAllByTestId('gantt-row-date');
  fireEvent.click(firstRow[0]);
  expect(screen.getByLabelText('A')).toBeInTheDocument();
});

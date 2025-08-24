'use client';

import { notFound } from 'next/navigation';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import ReactivePicker from '../../../components/ReactivePicker';
import VirtualizedGantt from '../../../components/VirtualizedGantt';
import ConflictsList from '../../../components/ConflictsList';
import { useSchedule, SchedulePoint } from '../../../lib/schedule';
import { isFeatureEnabled } from '../../../lib/featureFlags';

const queryClient = new QueryClient();

function SchedulerContent({ wo }: { wo: string }) {
  const { data } = useSchedule(wo);
  const [conflicts, setConflicts] = useState<string[]>([]);
  if (!data) return null;
  const { schedule, seed, objective } = data;

  const handleSelect = (point: SchedulePoint) => {
    setConflicts(point.conflicts ?? []);
  };

  const candidates = conflicts.map((c, i) => ({
    id: `c${i}`,
    label: c,
    explanation: `Conflict with ${c}`
  }));

  return (
    <main className="h-full flex flex-col">
      <h1 className="mb-4 text-xl font-semibold">Scheduler: {wo}</h1>
      <VirtualizedGantt data={schedule} onSelect={handleSelect} />
      <ReactivePicker wo={wo} />
      <ConflictsList candidates={candidates} />
      <footer className="mt-4 text-sm text-gray-500" data-testid="schedule-meta">
        Seed: {seed} Objective: {objective}
      </footer>
    </main>
  );
}

export default function SchedulerPage({ params }: { params: { wo: string } }) {
  if (!isFeatureEnabled('scheduler')) {
    notFound();
  }
  return (
    <QueryClientProvider client={queryClient}>
      <SchedulerContent wo={params.wo} />
    </QueryClientProvider>
  );
}


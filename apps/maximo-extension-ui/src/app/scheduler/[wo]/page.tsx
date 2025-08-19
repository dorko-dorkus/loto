'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Gantt from '../../../components/Gantt';
import { useSchedule } from '../../../lib/schedule';

const queryClient = new QueryClient();

function SchedulerContent({ wo }: { wo: string }) {
  const { data } = useSchedule(wo);
  if (!data) return null;
  const { schedule, seed, objective } = data;
  return (
    <main className="h-full flex flex-col">
      <h1 className="mb-4 text-xl font-semibold">Scheduler: {wo}</h1>
      <Gantt data={schedule} />
      <footer className="mt-4 text-sm text-gray-500" data-testid="schedule-meta">
        Seed: {seed} Objective: {objective}
      </footer>
    </main>
  );
}

export default function SchedulerPage({ params }: { params: { wo: string } }) {
  return (
    <QueryClientProvider client={queryClient}>
      <SchedulerContent wo={params.wo} />
    </QueryClientProvider>
  );
}


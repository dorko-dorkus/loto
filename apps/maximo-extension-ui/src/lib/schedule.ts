import { useQuery, UseQueryResult } from '@tanstack/react-query';

export interface SchedulePoint {
  date: string;
  p10: number;
  p50: number;
  p90: number;
  price: number;
  hats: number;
}

/**
 * Fetch schedule for a work order.
 */
export async function fetchSchedule(wo: string): Promise<SchedulePoint[]> {
  const res = await fetch('/schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workorder: wo })
  });
  if (!res.ok) throw new Error('Failed to fetch schedule');
  const data = await res.json();
  return data.schedule as SchedulePoint[];
}

/**
 * React Query hook for schedule data.
 */
export function useSchedule(wo: string): UseQueryResult<SchedulePoint[]> {
  return useQuery({ queryKey: ['schedule', wo], queryFn: () => fetchSchedule(wo) });
}


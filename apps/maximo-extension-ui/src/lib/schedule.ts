import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { apiFetch } from './api';
import { toastError } from './toast';
import { fetchSchedule as fetchScheduleMock } from '../mocks/schedule';

export interface SchedulePoint {
  date: string;
  p10: number;
  p50: number;
  p90: number;
  price: number;
  hats: number;
}

export interface ScheduleResponse {
  schedule: SchedulePoint[];
  seed: string;
  objective: number;
  blocked_by_parts: boolean;
  rulepack_sha256: string;
  rulepack_id?: string;
  rulepack_version?: string;
}

/**
 * Fetch schedule for a work order.
 */
export async function fetchSchedule(wo: string): Promise<ScheduleResponse> {
  const res = await apiFetch('/schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workorder: wo })
  });
  if (!res.ok) throw new Error('Failed to fetch schedule');
  const data = await res.json();
  return data as ScheduleResponse;
}

/**
 * React Query hook for schedule data.
 */
export function useSchedule(wo: string): UseQueryResult<ScheduleResponse> {
  const useApi = process.env.NEXT_PUBLIC_USE_API === 'true';
  return useQuery({
    queryKey: ['schedule', wo],
    queryFn: async () => {
      if (!useApi) return fetchScheduleMock(wo);
      try {
        return await fetchSchedule(wo);
      } catch (err) {
        toastError('Failed to fetch schedule');
        return fetchScheduleMock(wo);
      }
    }
  });
}


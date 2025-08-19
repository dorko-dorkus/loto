import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import type { HatSnapshot } from '../types/api';

/**
 * Fetch ranking snapshots for all hats from the API.
 */
async function fetchHats(): Promise<HatSnapshot[]> {
  const res = await fetch('/hats');
  if (!res.ok) {
    throw new Error('Failed to fetch hats');
  }
  return res.json();
}

/**
 * Query hook for hat ranking snapshots.
 */
export function useHats(): UseQueryResult<HatSnapshot[]> {
  return useQuery({ queryKey: ['hats'], queryFn: fetchHats });
}

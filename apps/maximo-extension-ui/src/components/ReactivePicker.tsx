import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import { toastError } from '../lib/toast';
import Skeleton from './Skeleton';
import { fetchHats } from '../mocks/hats';
import type { HatCandidate } from '../types/api';

async function fetchCandidatesApi(): Promise<HatCandidate[]> {
  const res = await apiFetch('/triage');
  if (!res.ok) throw new Error('Failed to fetch triage scores');
  return (await res.json()) as HatCandidate[];
}

export default function ReactivePicker({ wo }: { wo: string }) {
  const useApi = process.env.NEXT_PUBLIC_USE_API === 'true';
  const { data, isLoading } = useQuery({
    queryKey: ['reactive', wo],
    queryFn: async () => {
      if (!useApi) return fetchHats();
      try {
        return await fetchCandidatesApi();
      } catch (err) {
        toastError('Failed to fetch reactive candidates');
        return fetchHats();
      }
    }
  });
  if (isLoading) {
    return (
      <section className="mt-4">
        <h2 className="mb-2 text-lg font-semibold">Reactive candidates</h2>
        <ul className="space-y-1">
          {Array.from({ length: 3 }).map((_, idx) => (
            <li key={idx}>
              <Skeleton className="h-4 w-48" />
            </li>
          ))}
        </ul>
      </section>
    );
  }
  if (!data) return null;
  return (
    <section className="mt-4">
      <h2 className="mb-2 text-lg font-semibold">Reactive candidates</h2>
      <ul className="space-y-1">
        {data.map((hat) => {
          const delta = 1 - hat.c_r; // predicted finish delta from ranking coeff
          const penalized = (hat.rotation ?? 0) > 0;
          return (
            <li key={hat.hat_id} className={penalized ? 'text-red-600' : ''}>
              <span className="font-mono">{hat.hat_id}</span>
              {` \u2013 Δfinish ${delta.toFixed(2)}`}
              {penalized && (
                <span className="ml-2 text-xs">(rotation penalty)</span>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}


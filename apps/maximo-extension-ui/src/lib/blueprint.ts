import type { BlueprintData } from '../types/api';
import { apiFetch } from './api';

/**
 * Fetch blueprint data for a work order from the API.
 */
export async function fetchBlueprint(id: string): Promise<BlueprintData> {
  const res = await apiFetch('/blueprint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workorder_id: id })
  });
  if (!res.ok) {
    throw new Error('Failed to fetch blueprint');
  }
  return res.json();
}


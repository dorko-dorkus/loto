import type { BlueprintData } from '../types/api';

export async function fetchBlueprint(id: string): Promise<BlueprintData> {
  const res = await fetch('/blueprint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workorder_id: id })
  });
  if (!res.ok) {
    throw new Error('Failed to fetch blueprint');
  }
  return res.json();
}


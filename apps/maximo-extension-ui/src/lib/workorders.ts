import type { WorkOrderSummary } from '../types/api';
import { apiFetch } from './api';

/**
 * Fetch a work order from the API.
 */
export async function fetchWorkOrder(id: string): Promise<WorkOrderSummary> {
  const res = await apiFetch(`/workorders/${id}`);
  if (!res.ok) {
    throw new Error('Failed to fetch work order');
  }
  return res.json();
}


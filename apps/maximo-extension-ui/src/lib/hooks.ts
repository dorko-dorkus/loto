import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { fetchPortfolio, type PortfolioData } from '../mocks/portfolio';
import { fetchWorkOrder as fetchWorkOrderMock } from '../mocks/workorder';
import { fetchBlueprint as fetchBlueprintMock } from '../mocks/blueprint';
import type { WorkOrderSummary, BlueprintData } from '../types/api';
import { apiFetch } from './api';
import { fetchWorkOrder } from './workorders';
import { fetchBlueprint } from './blueprint';

/**
 * Fetch portfolio data from the API.
 */
async function fetchPortfolioApi(): Promise<PortfolioData> {
  const res = await apiFetch('/portfolio');
  if (!res.ok) {
    throw new Error('Failed to fetch portfolio');
  }
  return res.json();
}

/**
 * Query hook for portfolio data.
 *
 * When `NEXT_PUBLIC_USE_API` is set to `true`, data is retrieved from the
 * `/portfolio` API endpoint. Otherwise, mocked data is used.
 */
export function usePortfolioApi(): UseQueryResult<PortfolioData> {
  const useApi = process.env.NEXT_PUBLIC_USE_API === 'true';
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: async () => {
      if (!useApi) return fetchPortfolio();
      try {
        return await fetchPortfolioApi();
      } catch {
        return fetchPortfolio();
      }
    }
  });
}

// Preserve existing hook name for consumers expecting mocks.
export const usePortfolio = usePortfolioApi;

/**
 * Query hook for an individual work order.
 * @param id Work order identifier
 */
export function useWorkOrderApi(id: string): UseQueryResult<WorkOrderSummary> {
  const useApi = process.env.NEXT_PUBLIC_USE_API === 'true';
  return useQuery({
    queryKey: ['workOrder', id],
    queryFn: async () => {
      if (!useApi) return fetchWorkOrderMock(id);
      try {
        return await fetchWorkOrder(id);
      } catch {
        return fetchWorkOrderMock(id);
      }
    }
  });
}

export const useWorkOrder = useWorkOrderApi;

/**
 * Query hook for blueprint data of a work order.
 * @param id Work order identifier
 */
export function useBlueprintApi(id: string): UseQueryResult<BlueprintData> {
  const useApi = process.env.NEXT_PUBLIC_USE_API === 'true';
  return useQuery({
    queryKey: ['blueprint', id],
    queryFn: () => (useApi ? fetchBlueprint(id) : fetchBlueprintMock(id))
  });
}

export const useBlueprint = useBlueprintApi;

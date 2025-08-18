import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { fetchPortfolio, type PortfolioData } from '../mocks/portfolio';
import { fetchWorkOrder } from '../mocks/workorder';
import type { WorkOrderSummary } from '../types/api';

/**
 * Fetch portfolio data from the API.
 */
async function fetchPortfolioApi(): Promise<PortfolioData> {
  const res = await fetch('/portfolio');
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
    queryFn: useApi ? fetchPortfolioApi : fetchPortfolio
  });
}

// Preserve existing hook name for consumers expecting mocks.
export const usePortfolio = usePortfolioApi;

/**
 * Query hook for an individual work order.
 * @param id Work order identifier
 */
export function useWorkOrder(id: string): UseQueryResult<WorkOrderSummary> {
  return useQuery({ queryKey: ['workOrder', id], queryFn: () => fetchWorkOrder(id) });
}

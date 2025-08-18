import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { fetchPortfolio, type PortfolioData } from '../mocks/portfolio';
import { fetchWorkOrder } from '../mocks/workorder';
import { fetchBlueprint } from '../mocks/blueprint';
import type { WorkOrderSummary, BlueprintSummary } from '../types/api';

/**
 * Query hook for portfolio data.
 */
export function usePortfolio(): UseQueryResult<PortfolioData> {
  return useQuery({ queryKey: ['portfolio'], queryFn: fetchPortfolio });
}

/**
 * Query hook for an individual work order.
 * @param id Work order identifier
 */
export function useWorkOrder(id: string): UseQueryResult<WorkOrderSummary> {
  return useQuery({ queryKey: ['workOrder', id], queryFn: () => fetchWorkOrder(id) });
}

/**
 * Query hook for a work order blueprint.
 * @param id Work order identifier
 */
export function useBlueprint(id: string): UseQueryResult<BlueprintSummary> {
  return useQuery({ queryKey: ['blueprint', id], queryFn: () => fetchBlueprint(id) });
}

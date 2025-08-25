import { WorkOrderSummary } from '../types/api';

export async function fetchWorkOrder(id: string): Promise<WorkOrderSummary> {
  return {
    id,
    description: 'Example work order',
    status: 'WAPPR',
    maximoWo: `MX-${id.replace('WO-', '')}`,
    permitId: 'PRM-MOCK',
    permitVerified: false,
    permitRequired: true,
    isolationRef: 'ISO-MOCK',
    blocked_by_parts: false
  };
}


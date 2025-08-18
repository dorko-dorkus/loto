import { KpiItem } from '../components/KpiCards';
import { WorkOrderSummary } from '../types/api';

export interface PortfolioData {
  kpis: KpiItem[];
  workOrders: WorkOrderSummary[];
}

export async function fetchPortfolio(): Promise<PortfolioData> {
  return {
    kpis: [
      { label: 'Blueprints', value: 3 },
      { label: 'Active', value: 2 },
      { label: 'Completed', value: 1 }
    ],
    workOrders: [
      {
        id: 'WO-1',
        description: 'Pump replacement',
        status: 'Active',
        owner: 'Jane'
      },
      {
        id: 'WO-2',
        description: 'Motor upgrade',
        status: 'Draft',
        owner: 'John'
      },
      {
        id: 'WO-3',
        description: 'Energy audit',
        status: 'Completed',
        owner: 'Ben'
      }
    ]
  };
}

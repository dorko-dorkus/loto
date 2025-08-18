import { KpiItem } from '../components/KpiCards';

export interface Blueprint {
  name: string;
  status: string;
  owner: string;
}

export interface PortfolioData {
  kpis: KpiItem[];
  blueprints: Blueprint[];
}

export async function fetchPortfolio(): Promise<PortfolioData> {
  return {
    kpis: [
      { label: 'Blueprints', value: 3 },
      { label: 'Active', value: 2 },
      { label: 'Completed', value: 1 }
    ],
    blueprints: [
      { name: 'Pump replacement', status: 'Active', owner: 'Jane' },
      { name: 'Motor upgrade', status: 'Draft', owner: 'John' },
      { name: 'Energy audit', status: 'Completed', owner: 'Ben' }
    ]
  };
}

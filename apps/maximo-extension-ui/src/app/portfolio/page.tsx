'use client';

import { useState } from 'react';
import KpiCards, { KpiItem } from '../../components/KpiCards';
import { WorkOrderSummary } from '../../types/api';

const kpis: KpiItem[] = [
  { label: 'Blueprints', value: 3 },
  { label: 'Active', value: 2 },
  { label: 'Completed', value: 1 }
];

const workOrders: WorkOrderSummary[] = [
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
];

export default function PortfolioPage() {
  const [dense, setDense] = useState(false);

  return (
    <main>
      <h1 className="mb-4 text-xl font-semibold">Portfolio</h1>
      <KpiCards items={kpis} />
      <div className="mb-2 text-sm">
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={dense}
            onChange={(e) => setDense(e.target.checked)}
          />
          Dense table
        </label>
      </div>
      <table className="min-w-full border border-[var(--mxc-border)]">
        <thead className="bg-[var(--mxc-nav-bg)] text-left">
          <tr>
            <th className="px-4 py-2">Description</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Owner</th>
          </tr>
        </thead>
        <tbody>
          {workOrders.map((wo) => (
            <tr key={wo.id} className={dense ? 'text-sm' : undefined}>
              <td className={`px-4 ${dense ? 'py-1' : 'py-2'}`}>{wo.description}</td>
              <td className={`px-4 ${dense ? 'py-1' : 'py-2'}`}>{wo.status}</td>
              <td className={`px-4 ${dense ? 'py-1' : 'py-2'}`}>{wo.owner}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}


'use client';

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import KpiCards from '../../components/KpiCards';
import { usePortfolio } from '../../lib/hooks';

const queryClient = new QueryClient();

function PortfolioContent() {
  const [dense, setDense] = useState(false);
  const { data } = usePortfolio();

  if (!data) return null;

  return (
    <main>
      <h1 className="mb-4 text-xl font-semibold">Portfolio</h1>
      <KpiCards items={data.kpis} />
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
          {data.workOrders.map((wo) => (
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

export default function PortfolioPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <PortfolioContent />
    </QueryClientProvider>
  );
}


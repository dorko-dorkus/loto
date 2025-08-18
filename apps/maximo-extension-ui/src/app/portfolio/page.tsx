'use client';

import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import KpiCards from '../../components/KpiCards';
import { fetchPortfolio, PortfolioData } from '../../mocks/portfolio';

const queryClient = new QueryClient();

export default function PortfolioPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <Content />
    </QueryClientProvider>
  );
}

function Content() {
  const [dense, setDense] = useState(false);
  const { data } = useQuery<PortfolioData>({
    queryKey: ['portfolio'],
    queryFn: fetchPortfolio
  });

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
            <th className="px-4 py-2">Name</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Owner</th>
          </tr>
        </thead>
        <tbody>
          {data.blueprints.map((bp) => (
            <tr key={bp.name} className={dense ? 'text-sm' : undefined}>
              <td className={`px-4 ${dense ? 'py-1' : 'py-2'}`}>{bp.name}</td>
              <td className={`px-4 ${dense ? 'py-1' : 'py-2'}`}>{bp.status}</td>
              <td className={`px-4 ${dense ? 'py-1' : 'py-2'}`}>{bp.owner}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}


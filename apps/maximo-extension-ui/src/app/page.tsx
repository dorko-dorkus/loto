'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import KpiCards from '../components/KpiCards';
import Skeleton from '../components/Skeleton';
import { usePortfolio } from '../lib/hooks';

const queryClient = new QueryClient();

function HomeContent() {
  const { data, isLoading } = usePortfolio();

  if (isLoading) {
    return (
      <main>
        <h1 className="mb-4 text-xl font-semibold">Portfolio</h1>
        <KpiCards items={[]} loading />
        <Skeleton className="h-64 w-full" />
      </main>
    );
  }

  if (!data) return null;

  return (
    <main>
      <h1 className="mb-4 text-xl font-semibold">Portfolio</h1>
      <KpiCards items={data.kpis} />
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
            <tr key={wo.id}>
              <td className="px-4 py-2">{wo.description}</td>
              <td className="px-4 py-2">{wo.status}</td>
              <td className="px-4 py-2">{wo.owner}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

export default function Page() {
  return (
    <QueryClientProvider client={queryClient}>
      <HomeContent />
    </QueryClientProvider>
  );
}


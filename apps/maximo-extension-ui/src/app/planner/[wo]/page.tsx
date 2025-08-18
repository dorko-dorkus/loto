'use client';

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWorkOrder, useBlueprint } from '../../../lib/hooks';
import Exports from '../../../components/Exports';

const tabs = ['Plan', 'P&ID', 'Simulation', 'Impact'];

const queryClient = new QueryClient();

function PlannerContent({ wo }: { wo: string }) {
  const [activeTab, setActiveTab] = useState('Plan');
  const { data: workOrder } = useWorkOrder(wo);
  const { data: blueprint } = useBlueprint(wo);

  if (!workOrder) return null;

  const plan = blueprint?.steps ?? [];
  const unavailable = blueprint?.unavailable_assets ?? [];
  const impact = blueprint?.unit_mw_delta ?? {};

  return (
    <main className="h-full">
      <h1 className="mb-4 text-xl font-semibold">
        WO Planner: {workOrder.id}
      </h1>
      <Exports wo={workOrder.id} />
      <div className="flex h-full">
        <div className="flex-1 pr-4">
          <div role="tablist" className="mb-4 border-b">
            {tabs.map((tab) => (
              <button
                key={tab}
                role="tab"
                aria-selected={activeTab === tab}
                className={`mr-4 pb-2 ${activeTab === tab ? 'border-b-2 font-semibold' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>
          {activeTab === 'Plan' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">Step</th>
                  <th className="px-4 py-2">Component</th>
                  <th className="px-4 py-2">Method</th>
                </tr>
              </thead>
              <tbody>
                {plan.map((p, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2">{idx + 1}</td>
                    <td className="px-4 py-2">{p.component_id}</td>
                    <td className="px-4 py-2">{p.method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'P&ID' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">Step</th>
                  <th className="px-4 py-2">Component</th>
                  <th className="px-4 py-2">Method</th>
                </tr>
              </thead>
              <tbody>
                {plan.map((p, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2">{idx + 1}</td>
                    <td className="px-4 py-2">{p.component_id}</td>
                    <td className="px-4 py-2">{p.method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'Simulation' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">Unavailable Asset</th>
                </tr>
              </thead>
              <tbody>
                {unavailable.map((u) => (
                  <tr key={u}>
                    <td className="px-4 py-2">{u}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'Impact' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">Unit</th>
                  <th className="px-4 py-2">ΔMW</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(impact).map(([unit, delta]) => (
                  <tr key={unit}>
                    <td className="px-4 py-2">{unit}</td>
                    <td className="px-4 py-2">{delta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <aside className="w-64 shrink-0 border-l border-[var(--mxc-border)] bg-[var(--mxc-drawer-bg)] p-4 text-[var(--mxc-drawer-fg)]">
          Warnings placeholder
        </aside>
      </div>
    </main>
  );
}

export default function PlannerPage({ params }: { params: { wo: string } }) {
  return (
    <QueryClientProvider client={queryClient}>
      <PlannerContent wo={params.wo} />
    </QueryClientProvider>
  );
}


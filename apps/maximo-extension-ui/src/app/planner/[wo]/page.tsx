'use client';

import { useState } from 'react';
import { PlanStep, SimulationResult, ImpactRecord } from '../../../types/api';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWorkOrder } from '../../../lib/hooks';

const tabs = ['Plan', 'P&ID', 'Simulation', 'Impact'];

const queryClient = new QueryClient();

function PlannerContent({ wo }: { wo: string }) {
  const [activeTab, setActiveTab] = useState('Plan');
  const { data: workOrder } = useWorkOrder(wo);

  if (!workOrder) return null;

  const plan: PlanStep[] = [
    { step: 1, description: 'Example step', resources: 'None' }
  ];

  const simulations: SimulationResult[] = [
    {
      id: 1,
      deltaTime: '+1d',
      deltaCost: '+$100',
      readiness: 'High',
      isolation: true
    }
  ];

  const impact: ImpactRecord[] = [
    { metric: 'Downtime (hrs)', before: 10, after: 8, delta: -2 }
  ];

  return (
    <main className="h-full">
      <h1 className="mb-4 text-xl font-semibold">
        WO Planner: {workOrder.id}
      </h1>
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
                  <th className="px-4 py-2">Description</th>
                  <th className="px-4 py-2">Resources</th>
                </tr>
              </thead>
              <tbody>
                {plan.map((p) => (
                  <tr key={p.step}>
                    <td className="px-4 py-2">{p.step}</td>
                    <td className="px-4 py-2">{p.description}</td>
                    <td className="px-4 py-2">{p.resources}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'P&ID' && <div>P&amp;ID placeholder</div>}
          {activeTab === 'Simulation' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">ΔTime</th>
                  <th className="px-4 py-2">ΔCost</th>
                  <th className="px-4 py-2">Readiness</th>
                  <th className="px-4 py-2">Isolation subset?</th>
                </tr>
              </thead>
              <tbody>
                {simulations.map((s) => (
                  <tr key={s.id}>
                    <td className="px-4 py-2">{s.deltaTime}</td>
                    <td className="px-4 py-2">{s.deltaCost}</td>
                    <td className="px-4 py-2">{s.readiness}</td>
                    <td className="px-4 py-2">{s.isolation ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'Impact' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">Metric</th>
                  <th className="px-4 py-2">Before</th>
                  <th className="px-4 py-2">After</th>
                  <th className="px-4 py-2">Δ</th>
                </tr>
              </thead>
              <tbody>
                {impact.map((i) => (
                  <tr key={i.metric}>
                    <td className="px-4 py-2">{i.metric}</td>
                    <td className="px-4 py-2">{i.before}</td>
                    <td className="px-4 py-2">{i.after}</td>
                    <td className="px-4 py-2">{i.delta}</td>
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


'use client';

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWorkOrder, useBlueprint } from '../../../lib/hooks';
import Exports from '../../../components/Exports';
import CommitPanel from './CommitPanel';
import PidTab from './PidTab';
import type { MaterialStatus } from '../../../types/api';

const tabs = ['Plan', 'Materials', 'P&ID', 'Simulation', 'Impact', 'Commit'];

const queryClient = new QueryClient();

function PlannerContent({ wo }: { wo: string }) {
  const [activeTab, setActiveTab] = useState('Plan');
  const { data: workOrder } = useWorkOrder(wo);
  const { data: blueprint } = useBlueprint(wo);

  if (!workOrder) return null;

  const plan = blueprint?.steps ?? [];
  const unavailable = blueprint?.unavailable_assets ?? [];
  const impact = blueprint?.unit_mw_delta ?? {};
  const materials = blueprint?.parts_status ?? {};

  const statusStyles: Record<MaterialStatus, string> = {
    ok: 'bg-green-100 text-green-800',
    low: 'bg-yellow-100 text-yellow-800',
    short: 'bg-red-100 text-red-800',
    rfq: 'bg-blue-100 text-blue-800',
    parked: 'bg-gray-100 text-gray-800'
  };

  const statusLabels: Record<MaterialStatus, string> = {
    ok: 'OK',
    low: 'Low',
    short: 'Short',
    rfq: 'RFQ',
    parked: 'Parked'
  };

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
          {activeTab === 'Materials' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">Item</th>
                  <th className="px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(materials).map(([item, status]) => (
                  <tr key={item}>
                    <td className="px-4 py-2">{item}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${statusStyles[status as MaterialStatus]}`}
                      >
                        {statusLabels[status as MaterialStatus]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'P&ID' && <PidTab wo={wo} />}
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
          {activeTab === 'Commit' && <CommitPanel wo={wo} />}
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


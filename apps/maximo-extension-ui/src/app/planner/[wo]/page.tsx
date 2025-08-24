'use client';

import { useState, useMemo } from 'react';
import { notFound } from 'next/navigation';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWorkOrderApi, useBlueprintApi } from '../../../lib/hooks';
import Exports from '../../../components/Exports';
import CommitPanel from './CommitPanel';
import PidTab from './PidTab';
import type { MaterialStatus } from '../../../types/api';
import { isFeatureEnabled } from '../../../lib/featureFlags';

const tabs = ['Plan', 'Materials', 'P&ID', 'Simulation', 'Impact', 'Commit'];

const queryClient = new QueryClient();

function PlannerContent({ wo }: { wo: string }) {
  const [activeTab, setActiveTab] = useState('Plan');
  const [planFilter, setPlanFilter] = useState('');
  const { data: workOrder } = useWorkOrderApi(wo);
  const { data: blueprint } = useBlueprintApi(wo);

  const plan = blueprint?.steps ?? [];
  const unavailable = blueprint?.unavailable_assets ?? [];
  const impact = blueprint?.unit_mw_delta ?? {};
  const materials = blueprint?.parts_status ?? {};
  const simStatus = unavailable.length
    ? 'red'
    : blueprint?.blocked_by_parts
      ? 'yellow'
      : 'green';

  const filteredPlan = useMemo(
    () =>
      plan.filter(
        (p) =>
          p.component_id.toLowerCase().includes(planFilter.toLowerCase()) ||
          p.method.toLowerCase().includes(planFilter.toLowerCase())
      ),
    [plan, planFilter]
  );

  if (!workOrder) return null;

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
            <div>
              <div className="mb-2 flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Search steps"
                  value={planFilter}
                  onChange={(e) => setPlanFilter(e.target.value)}
                  className="border px-2 py-1"
                />
                <button
                  type="button"
                  className="badge"
                  onClick={() => {
                    const txt = filteredPlan
                      .map(
                        (p, idx) => `${idx + 1}\t${p.component_id}\t${p.method}`
                      )
                      .join('\n');
                    navigator.clipboard?.writeText(txt).catch(() => {});
                  }}
                >
                  Copy
                </button>
                <button
                  type="button"
                  className="badge"
                  onClick={() => {
                    const csv =
                      'Step,Component,Method\n' +
                      filteredPlan
                        .map(
                          (p, idx) =>
                            `${idx + 1},${p.component_id},${p.method}`
                        )
                        .join('\n');
                    const blob = new Blob([csv], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `WO-${wo}_plan.csv`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    URL.revokeObjectURL(url);
                  }}
                >
                  Export CSV
                </button>
              </div>
              <table className="min-w-full border border-[var(--mxc-border)]">
                <thead className="bg-[var(--mxc-nav-bg)] text-left">
                  <tr>
                    <th className="px-4 py-2">Step</th>
                    <th className="px-4 py-2">Component</th>
                    <th className="px-4 py-2">Method</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPlan.map((p, idx) => (
                    <tr key={idx}>
                      <td className="px-4 py-2">{idx + 1}</td>
                      <td className="px-4 py-2">{p.component_id}</td>
                      <td className="px-4 py-2">{p.method}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {activeTab === 'Materials' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">Item</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Flag</th>
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
                    <td className="px-4 py-2">
                      {status === 'short' && 'Stock-out'}
                      {status === 'low' && 'Below reorder'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'P&ID' && <PidTab wo={wo} />}
          {activeTab === 'Simulation' && (
            <div>
              <div className="mb-2 font-semibold">
                Status:{' '}
                <span
                  className={
                    simStatus === 'green'
                      ? 'text-green-600'
                      : simStatus === 'yellow'
                        ? 'text-yellow-600'
                        : 'text-red-600'
                  }
                >
                  {simStatus}
                </span>
              </div>
              <ul className="mb-2 list-disc pl-5">
                {unavailable.length === 0 && <li>No warnings</li>}
                {unavailable.map((u) => (
                  <li key={u}>{u}</li>
                ))}
              </ul>
            </div>
          )}
          {activeTab === 'Impact' && (
            <table className="min-w-full border border-[var(--mxc-border)]">
              <thead className="bg-[var(--mxc-nav-bg)] text-left">
                <tr>
                  <th className="px-4 py-2">Unit</th>
                  <th className="px-4 py-2">ΔMW</th>
                  <th className="px-4 py-2">Risk</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(impact).map(([unit, delta]) => {
                  const risk = Math.abs(delta) > 10 ? 'High' : 'Low';
                  const riskClass =
                    risk === 'High'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-green-100 text-green-800';
                  return (
                    <tr key={unit}>
                      <td className="px-4 py-2">{unit}</td>
                      <td className="px-4 py-2">{delta}</td>
                      <td className="px-4 py-2">
                        <span
                          className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${riskClass}`}
                        >
                          {risk}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
          {activeTab === 'Commit' && <CommitPanel wo={wo} simOk={simStatus === 'green'} />}
        </div>
        <aside className="w-64 shrink-0 border-l border-[var(--mxc-border)] bg-[var(--mxc-drawer-bg)] p-4 text-[var(--mxc-drawer-fg)]">
          Warnings placeholder
        </aside>
      </div>
    </main>
  );
}

export default function PlannerPage({ params }: { params: { wo: string } }) {
  if (!isFeatureEnabled('planner')) {
    notFound();
  }
  return (
    <QueryClientProvider client={queryClient}>
      <PlannerContent wo={params.wo} />
    </QueryClientProvider>
  );
}


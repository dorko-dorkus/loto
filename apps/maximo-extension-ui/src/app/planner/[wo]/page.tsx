'use client';

import { useState } from 'react';

const tabs = ['Plan', 'P&ID', 'Simulation', 'Impact'];

export default function PlannerPage({ params }: { params: { wo: string } }) {
  const [activeTab, setActiveTab] = useState('Plan');

  return (
    <main className="h-full">
      <h1 className="mb-4 text-xl font-semibold">WO Planner: {params.wo}</h1>
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
                <tr>
                  <td className="px-4 py-2">1</td>
                  <td className="px-4 py-2">Example step</td>
                  <td className="px-4 py-2">None</td>
                </tr>
              </tbody>
            </table>
          )}
          {activeTab === 'P&ID' && <div>P&amp;ID placeholder</div>}
          {activeTab === 'Simulation' && <div>Simulation placeholder</div>}
          {activeTab === 'Impact' && <div>Impact placeholder</div>}
        </div>
        <aside className="w-64 shrink-0 border-l border-[var(--mxc-border)] bg-[var(--mxc-drawer-bg)] p-4 text-[var(--mxc-drawer-fg)]">
          Warnings placeholder
        </aside>
      </div>
    </main>
  );
}


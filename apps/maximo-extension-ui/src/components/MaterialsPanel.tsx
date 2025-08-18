import React from 'react';
import { InventoryItem, InventoryStatus } from '../types/api';
import ActionBar from './ActionBar';

interface MaterialsPanelProps {
  items: InventoryItem[];
}

const statusStyles: Record<InventoryStatus, { icon: string; label: string; color: string }> = {
  ready: { icon: '✓', label: 'Ready', color: 'text-green-600' },
  short: { icon: '⚠️', label: 'Short', color: 'text-red-600' },
  ordered: { icon: '⏳', label: 'Ordered', color: 'text-blue-600' }
};

export default function MaterialsPanel({ items }: MaterialsPanelProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="overflow-hidden rounded-[var(--mxc-radius-md)] border border-[var(--mxc-border)]">
        <table
          aria-label="Materials"
          tabIndex={0}
          className="min-w-full divide-y divide-[var(--mxc-border)] text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--mxc-border)]"
        >
          <thead className="bg-[var(--mxc-bg)]">
            <tr>
              <th scope="col" className="px-4 py-2 text-left font-medium">
                Item
              </th>
              <th scope="col" className="px-4 py-2 text-right font-medium">
                Required
              </th>
              <th scope="col" className="px-4 py-2 text-right font-medium">
                On-hand
              </th>
              <th scope="col" className="px-4 py-2 text-left font-medium">
                ETA
              </th>
              <th scope="col" className="px-4 py-2 text-left font-medium">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--mxc-border)]">
            {items.map(({ item, required, onHand, eta, status }) => {
              const { icon, label, color } = statusStyles[status];
              return (
                <tr key={item} className="bg-[var(--mxc-bg)]">
                  <td className="px-4 py-2">{item}</td>
                  <td className="px-4 py-2 text-right">{required}</td>
                  <td className="px-4 py-2 text-right">{onHand}</td>
                  <td className="px-4 py-2">{eta ?? '—'}</td>
                  <td className="px-4 py-2">
                    <span className={`flex items-center gap-1 font-medium ${color}`}>
                      <span aria-hidden="true">{icon}</span>
                      <span>{label}</span>
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <ActionBar />
    </div>
  );
}


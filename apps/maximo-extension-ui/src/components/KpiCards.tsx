import React from 'react';

export interface KpiItem {
  label: string;
  value: string | number;
}

interface KpiCardsProps {
  items: KpiItem[];
}

export default function KpiCards({ items }: KpiCardsProps) {
  return (
    <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
      {items.map(({ label, value }) => (
        <div
          key={label}
          className="rounded-[var(--mxc-radius-md)] border border-[var(--mxc-border)] p-4 text-center shadow-[var(--mxc-shadow-sm)]"
        >
          <div className="text-2xl font-semibold">{value}</div>
          <div className="mt-2 text-sm">{label}</div>
        </div>
      ))}
    </div>
  );
}


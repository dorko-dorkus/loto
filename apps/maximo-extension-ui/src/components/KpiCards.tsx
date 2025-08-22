import React from 'react';
import Skeleton from './Skeleton';

export interface KpiItem {
  label: string;
  value: string | number;
}

interface KpiCardsProps {
  items: KpiItem[];
  loading?: boolean;
}

export default function KpiCards({ items, loading = false }: KpiCardsProps) {
  if (loading) {
    const placeholders = items.length || 3;
    return (
      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {Array.from({ length: placeholders }).map((_, idx) => (
          <div
            key={idx}
            className="rounded-[var(--mxc-radius-md)] border border-[var(--mxc-border)] p-4 text-center shadow-[var(--mxc-shadow-sm)]"
          >
            <Skeleton className="mx-auto h-8 w-12" />
            <Skeleton className="mx-auto mt-2 h-4 w-24" />
          </div>
        ))}
      </div>
    );
  }
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


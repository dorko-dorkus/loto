import React from 'react';
import clsx from 'clsx';

export interface StepperProps {
  steps: string[];
  active: number;
  className?: string;
}

export default function Stepper({ steps, active, className }: StepperProps) {
  return (
    <ol className={clsx('flex gap-2', className)}>
      {steps.map((step, index) => (
        <li
          key={step}
          className={clsx(
            'rounded px-3 py-1',
            index === active
              ? 'bg-[var(--mxc-topbar-bg)] text-[var(--mxc-topbar-fg)]'
              : 'bg-[var(--mxc-sheet)] text-[var(--mxc-fg-subtle)]'
          )}
        >
          {step}
        </li>
      ))}
    </ol>
  );
}

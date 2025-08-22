'use client';

import React, { useRef, useState } from 'react';
import Button from './Button';
import { apiFetch } from '../lib/api';
import { toastError } from '../lib/toast';

interface WizardExportProps {
  plan: unknown;
}

export default function WizardExport({ plan }: WizardExportProps) {
  const [hash, setHash] = useState<string | null>(null);
  const [seed, setSeed] = useState<string | null>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);

  async function handleExport(format: 'pdf' | 'json') {
    try {
      const res = await apiFetch('/blueprint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: format === 'pdf' ? 'application/pdf' : 'application/json'
        },
        body: JSON.stringify(plan)
      });
      if ('ok' in res && !res.ok) throw new Error('Failed to export plan');

      const h = res.headers.get('x-loto-hash');
      const s = res.headers.get('x-loto-seed');
      if (h) setHash(h);
      if (s) setSeed(s);

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const ext = format === 'pdf' ? 'pdf' : 'json';
      const a = document.createElement('a');
      a.href = url;
      a.download = `plan_${h ?? 'unknown'}.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      toastError('Failed to export plan');
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (!toolbarRef.current) return;
    const buttons = toolbarRef.current.querySelectorAll<HTMLButtonElement>('button');
    const currentIndex = Array.from(buttons).indexOf(
      document.activeElement as HTMLButtonElement
    );
    if (e.key === 'ArrowRight') {
      const next = buttons[(currentIndex + 1) % buttons.length];
      next.focus();
      e.preventDefault();
    } else if (e.key === 'ArrowLeft') {
      const prev = buttons[(currentIndex - 1 + buttons.length) % buttons.length];
      prev.focus();
      e.preventDefault();
    }
  }

  return (
    <div
      ref={toolbarRef}
      role="toolbar"
      aria-label="Export options"
      onKeyDown={handleKeyDown}
      className="mb-4 flex items-center space-x-2"
    >
      <Button aria-label="Export PDF" onClick={() => handleExport('pdf')}>
        Export PDF
      </Button>
      <Button aria-label="Export JSON" onClick={() => handleExport('json')}>
        Export JSON
      </Button>
      {hash && <span>Hash: {hash}</span>}
      {seed && <span>Seed: {seed}</span>}
    </div>
  );
}


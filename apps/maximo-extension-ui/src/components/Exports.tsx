'use client';

import React, { useState } from 'react';
import Button from './Button';
import { exportPid } from '../lib/exportPid';

interface ExportProps {
  wo: string;
}

export default function Exports({ wo }: ExportProps) {
  const [hash, setHash] = useState<string | null>(null);
  const [seed, setSeed] = useState<string | null>(null);

  async function handleExport(format: 'pdf' | 'json') {
    const res = await fetch('/blueprint', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: format === 'pdf' ? 'application/pdf' : 'application/json'
      },
      body: JSON.stringify({ workorder_id: wo })
    });
    if (!res.ok) return;

    const h = res.headers.get('x-loto-hash');
    const s = res.headers.get('x-loto-seed');
    if (h) setHash(h);
    if (s) setSeed(s);

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const ext = format === 'pdf' ? 'pdf' : 'json';
    const a = document.createElement('a');
    a.href = url;
    a.download = `WO-${wo}_${h ?? 'unknown'}.${ext}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function handlePidA3() {
    const res = await fetch('/pid/pdf', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/pdf'
      },
      body: JSON.stringify({ workorder_id: wo })
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `WO-${wo}_pid_a3.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="mb-4 flex items-center space-x-2">
      <Button aria-label="Export PDF" onClick={() => handleExport('pdf')}>
        Export PDF
      </Button>
      <Button aria-label="Export JSON" onClick={() => handleExport('json')}>
        Export JSON
      </Button>
      <Button
        aria-label="Export P&ID"
        onClick={() => exportPid(`WO-${wo}_pid.pdf`)}
      >
        Export P&ID
      </Button>
      <Button aria-label="Export P&ID (A3)" onClick={handlePidA3}>
        Export P&ID (A3)
      </Button>
      {hash && <span>Hash: {hash}</span>}
      {seed && <span>Seed: {seed}</span>}
    </div>
  );
}

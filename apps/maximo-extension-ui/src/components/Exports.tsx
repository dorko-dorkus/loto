import React, { useState } from 'react';
import Button from './Button';

interface ExportsProps {
  wo: string;
}

export default function Exports({ wo }: ExportsProps) {
  const [hash, setHash] = useState<string | null>(null);

  async function handleExport(kind: 'pdf' | 'json') {
    const res = await fetch(`/api/workorders/${wo}/export.${kind}`);
    const blob = await res.blob();
    const responseHash = res.headers.get('x-hash') || res.headers.get('x-seed') || '';
    setHash(responseHash);

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${wo}-${responseHash}.${kind}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <Button onClick={() => handleExport('pdf')}>Export PDF</Button>
        <Button onClick={() => handleExport('json')}>Export JSON</Button>
      </div>
      {hash && (
        <div role="status" className="text-sm">
          Seed: {hash}
        </div>
      )}
    </div>
  );
}


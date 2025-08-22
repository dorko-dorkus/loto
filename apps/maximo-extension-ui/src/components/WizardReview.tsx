'use client';

import React, { useEffect } from 'react';

interface ParsedFile {
  name: string;
  data: Record<string, unknown>[];
}

interface WizardReviewProps {
  files: ParsedFile[];
  requiredFields: string[];
  accepted: boolean;
  setAccepted: (accepted: boolean) => void;
}

export default function WizardReview({
  files,
  requiredFields,
  accepted,
  setAccepted
}: WizardReviewProps) {
  useEffect(() => {
    const stored = localStorage.getItem('wizardReviewAccepted');
    if (stored !== null) setAccepted(stored === 'true');
  }, [setAccepted]);

  useEffect(() => {
    localStorage.setItem('wizardReviewAccepted', String(accepted));
  }, [accepted]);

  const hasError = (row: Record<string, unknown>, header: string) =>
    requiredFields.includes(header) &&
    (row[header] === undefined || row[header] === null || row[header] === '');

  return (
    <div>
      {files.map((file) => {
        const rows = file.data.slice(0, 5);
        const headers = Array.from(
          new Set(rows.flatMap((r) => Object.keys(r)))
        );
        return (
          <div key={file.name} className="mb-4">
            <h2 className="font-bold">{file.name}</h2>
            <table className="min-w-full border" data-testid={`preview-${file.name}`}>
              <thead>
                <tr>
                  {headers.map((header) => (
                    <th key={header} className="border px-2 py-1 text-left">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => (
                  <tr key={idx}>
                    {headers.map((header) => (
                      <td
                        key={header}
                        className={hasError(row, header) ? 'bg-red-100 border px-2 py-1' : 'border px-2 py-1'}
                      >
                        {String((row as Record<string, unknown>)[header] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
      <label className="mt-4 block">
        <input
          type="checkbox"
          checked={accepted}
          onChange={(e) => setAccepted(e.target.checked)}
          data-testid="wizard-review-accept"
        />
        <span className="ml-2">I accept the uploaded data</span>
      </label>
    </div>
  );
}


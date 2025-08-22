'use client';

import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/api';

interface ParsedFile {
  name: string;
  data: Record<string, unknown>[];
}

interface WizardGenerateProps {
  data: ParsedFile[];
  setPlan: (plan: unknown) => void;
  setStep: (step: number) => void;
}

export default function WizardGenerate({ data, setPlan, setStep }: WizardGenerateProps) {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function generate() {
      setLoading(true);
      try {
        const res = await apiFetch('/schedule', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ files: data })
        });
        if (!cancelled && res.ok) {
          const plan = await res.json();
          setPlan(plan);
          localStorage.setItem('wizardPlan', JSON.stringify(plan));
          setStep(3);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    generate();
    return () => {
      cancelled = true;
    };
  }, [data, setPlan, setStep]);

  if (!loading) return null;
  return <div data-testid="wizard-generate-spinner">Loading...</div>;
}


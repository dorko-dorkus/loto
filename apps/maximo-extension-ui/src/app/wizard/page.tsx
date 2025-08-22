'use client';

import { useEffect, useState } from 'react';
import Stepper from '../../components/Stepper';
import WizardExport from '../../components/WizardExport';

interface WizardData {
  name: string;
  age: string;
}

const steps = ['Step One', 'Step Two', 'Step Three', 'Export'];

export default function WizardPage() {
  const [step, setStep] = useState(0);
  const [data, setData] = useState<WizardData>({ name: '', age: '' });

  // Load initial state from localStorage
  useEffect(() => {
    const storedStep = window.localStorage.getItem('wizard-step');
    const storedData = window.localStorage.getItem('wizard-data');
    if (storedStep) {
      const parsed = parseInt(storedStep, 10);
      if (!Number.isNaN(parsed)) setStep(parsed);
    }
    if (storedData) {
      try {
        const parsed = JSON.parse(storedData) as WizardData;
        setData(parsed);
      } catch {
        /* ignore bad data */
      }
    }
  }, []);

  // Persist step to storage
  useEffect(() => {
    window.localStorage.setItem('wizard-step', String(step));
  }, [step]);

  // Persist data to storage
  useEffect(() => {
    window.localStorage.setItem('wizard-data', JSON.stringify(data));
  }, [data]);

  const StepOne = () => (
    <div>
      <label>
        Name
        <input
          aria-label="name"
          value={data.name}
          onChange={(e) => setData({ ...data, name: e.target.value })}
        />
      </label>
      <button onClick={() => setStep(1)}>Next</button>
    </div>
  );

  const StepTwo = () => (
    <div>
      <label>
        Age
        <input
          aria-label="age"
          value={data.age}
          onChange={(e) => setData({ ...data, age: e.target.value })}
        />
      </label>
      <button onClick={() => setStep(2)}>Next</button>
    </div>
  );

  const StepThree = () => (
    <div>
      <p>
        Name: {data.name || '-'}, Age: {data.age || '-'}
      </p>
      <button onClick={() => setStep(3)}>Next</button>
    </div>
  );

  const StepFour = () => (
    <div>
      <WizardExport plan={data} />
      <button onClick={() => setStep(0)}>Restart</button>
    </div>
  );

  const stepComponents = [
    <StepOne key={0} />,
    <StepTwo key={1} />,
    <StepThree key={2} />,
    <StepFour key={3} />
  ];

  return (
    <main>
      <Stepper steps={steps} active={step} />
      {stepComponents[step]}
    </main>
  );
}


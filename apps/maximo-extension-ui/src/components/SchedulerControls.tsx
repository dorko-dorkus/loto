'use client';
import React, { useState } from 'react';

export default function SchedulerControls() {
  const [objective, setObjective] = useState('speed');
  const [alpha, setAlpha] = useState(0.5);
  const [riskTarget, setRiskTarget] = useState(0.1);
  const [samples, setSamples] = useState(100);
  const [seed, setSeed] = useState(0);

  return (
    <form className="space-y-4">
      <div>
        <label htmlFor="objective" className="mr-2">
          Objective
        </label>
        <select
          id="objective"
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          className="border px-2 py-1"
        >
          <option value="speed">Speed</option>
          <option value="cost">Cost</option>
        </select>
      </div>
      <div>
        <label htmlFor="alpha" className="mr-2">
          α (spot exposure)
        </label>
        <input
          id="alpha"
          type="number"
          step="0.01"
          value={alpha}
          onChange={(e) => setAlpha(parseFloat(e.target.value))}
          className="border px-2 py-1"
        />
        <span data-testid="alpha-display" className="ml-2">
          {alpha}
        </span>
      </div>
      <div>
        <label htmlFor="riskTarget" className="mr-2">
          Risk target
        </label>
        <input
          id="riskTarget"
          type="number"
          step="0.01"
          value={riskTarget}
          onChange={(e) => setRiskTarget(parseFloat(e.target.value))}
          className="border px-2 py-1"
        />
      </div>
      <div>
        <label htmlFor="samples" className="mr-2">
          N samples
        </label>
        <input
          id="samples"
          type="number"
          value={samples}
          onChange={(e) => setSamples(parseInt(e.target.value, 10))}
          className="border px-2 py-1"
        />
      </div>
      <div>
        <label htmlFor="seed" className="mr-2">
          Seed
        </label>
        <input
          id="seed"
          type="number"
          value={seed}
          onChange={(e) => setSeed(parseInt(e.target.value, 10))}
          className="border px-2 py-1"
        />
      </div>
    </form>
  );
}

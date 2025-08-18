import React, { useState } from 'react';
import { fetchRecommendedSet } from '../mocks/bundling';

interface Candidate {
  id: string;
  label: string;
  explanation: string;
}

interface ConflictsListProps {
  candidates: Candidate[];
}

export default function ConflictsList({ candidates }: ConflictsListProps) {
  const [selected, setSelected] = useState<string[]>([]);

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleRecommend = async () => {
    const rec = await fetchRecommendedSet();
    setSelected(rec);
  };

  return (
    <div>
      <ul>
        {candidates.map(({ id, label, explanation }) => (
          <li key={id} className="mb-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={selected.includes(id)}
                onChange={() => toggle(id)}
                aria-label={label}
              />
              <span>{label}</span>
            </label>
            <p className="ml-6 text-sm text-gray-600">{explanation}</p>
          </li>
        ))}
      </ul>
      <button type="button" aria-label="Select recommended set" onClick={handleRecommend}>
        Select recommended set
      </button>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import Button from './Button';

export default function DensityToggle() {
  const [density, setDensity] = useState<'comfortable' | 'compact'>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('density');
      if (stored === 'comfortable' || stored === 'compact') return stored;
    }
    return 'comfortable';
  });

  useEffect(() => {
    document.documentElement.dataset.density = density;
    localStorage.setItem('density', density);
  }, [density]);

  return (
    <Button
      aria-label="Toggle density"
      onClick={() => setDensity(density === 'compact' ? 'comfortable' : 'compact')}
    >
      {density === 'compact' ? 'Comfortable density' : 'Compact density'}
    </Button>
  );
}

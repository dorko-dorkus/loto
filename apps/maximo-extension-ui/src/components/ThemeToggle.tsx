'use client';

import { useEffect, useState } from 'react';
import Button from './Button';

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem('theme');
    const initial =
      stored === 'light' || stored === 'dark'
        ? stored
        : window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light';
    setTheme(initial);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }, [mounted, theme]);

  if (!mounted) {
    // avoid mismatched text during hydration
    return <Button aria-label="Toggle dark mode" />;
  }

  return (
    <Button aria-label="Toggle dark mode" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      {theme === 'dark' ? 'Light mode' : 'Dark mode'}
    </Button>
  );
}

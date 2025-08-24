'use client';
import { useEffect } from 'react';

export default function PrintHotkey() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'p' && !e.metaKey && !e.ctrlKey && !e.altKey && !e.shiftKey) {
        const target = e.target as HTMLElement | null;
        if (
          target &&
          (target instanceof HTMLInputElement ||
            target instanceof HTMLTextAreaElement ||
            target.isContentEditable)
        ) {
          return;
        }
        e.preventDefault();
        window.print();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return null;
}

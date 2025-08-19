import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class', '[data-theme="dark"]'],
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'var(--mxc-bg)',
        foreground: 'var(--mxc-fg)',
        'status-success': 'var(--mxc-status-success)',
        'status-info': 'var(--mxc-status-info)',
        'status-warning': 'var(--mxc-status-warning)',
        'status-critical': 'var(--mxc-status-critical)'
      }
    }
  },
  plugins: [require('tailwindcss-animate')]
};

export default config;

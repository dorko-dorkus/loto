import type { FC } from 'react';

interface FooterProps {
  version: string;
}

const Footer: FC<FooterProps> = ({ version }) => {
  return (
    <footer className="h-8 border-t border-[var(--mxc-border)] text-xs text-[var(--mxc-nav-fg)] flex items-center justify-center">
      <span>Version: {version}</span>
    </footer>
  );
};

export default Footer;

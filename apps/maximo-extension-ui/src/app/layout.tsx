import type { ReactNode } from 'react';
import '../styles/globals.css';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-screen">
        <div className="flex min-h-screen flex-col">
          <header className="flex h-12 items-center bg-[var(--mxc-topbar-bg)] px-4 text-[var(--mxc-topbar-fg)]">
            <span className="font-semibold">Maximo Extension</span>
          </header>
          <div className="flex flex-1 overflow-hidden">
            <nav className="w-56 shrink-0 border-r border-[var(--mxc-border)] bg-[var(--mxc-nav-bg)] p-4 text-[var(--mxc-nav-fg)]">
              <ul>
                <li className="font-medium">Portfolio</li>
              </ul>
            </nav>
            <div className="flex-1 overflow-auto p-4">{children}</div>
            <aside className="w-64 shrink-0 border-l border-[var(--mxc-border)] bg-[var(--mxc-drawer-bg)] p-4 text-[var(--mxc-drawer-fg)]">
              {/* Right drawer placeholder */}
            </aside>
          </div>
        </div>
      </body>
    </html>
  );
}

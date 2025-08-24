import type { ReactNode } from 'react';
import '../styles/globals.css';
import ThemeToggle from '../components/ThemeToggle';
import DensityToggle from '../components/DensityToggle';
import Footer from '../components/Footer';
import PrintHotkey from '../components/PrintHotkey';
import { apiFetch } from '../lib/api';

export default async function RootLayout({ children }: { children: ReactNode }) {
  let version = 'unknown';
  try {
    const res = await apiFetch('/version');
    const data = (await res.json()) as { version: string; git_sha?: string };
    version = data.git_sha ? `${data.version} (${data.git_sha})` : data.version;
  } catch {
    /* ignore */
  }
  return (
    <html lang="en" className="h-full">
      <body className="min-h-screen">
        <PrintHotkey />
        <div className="flex min-h-screen flex-col">
          <header className="flex h-12 items-center justify-between bg-[var(--mxc-topbar-bg)] px-4 text-[var(--mxc-topbar-fg)] print:hidden">
            <span className="font-semibold">Maximo Extension</span>
            <div className="flex gap-2">
              <ThemeToggle />
              <DensityToggle />
            </div>
          </header>
          <div className="flex flex-1 overflow-hidden">
            <nav className="w-56 shrink-0 border-r border-[var(--mxc-border)] bg-[var(--mxc-nav-bg)] p-4 text-[var(--mxc-nav-fg)] print:hidden">
              <ul>
                <li className="font-medium">Portfolio</li>
              </ul>
            </nav>
            <div className="flex-1 overflow-auto p-4 print:p-0">{children}</div>
            <aside className="w-64 shrink-0 border-l border-[var(--mxc-border)] bg-[var(--mxc-drawer-bg)] p-4 text-[var(--mxc-drawer-fg)] print:hidden">
              {/* Right drawer placeholder */}
            </aside>
          </div>
          <div className="print:hidden">
            <Footer version={version} />
          </div>
        </div>
      </body>
    </html>
  );
}

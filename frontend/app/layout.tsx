import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Escalation Tournament Platform',
  description: 'Modular infrastructure for multi-format competitive events.'
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-slate-950 text-slate-100">
      <body className="min-h-screen font-sans antialiased">
        <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
          <div className="mx-auto flex max-w-5xl flex-col gap-2 px-6 py-8 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-widest text-slate-400">Escalation Ops</p>
              <h1 className="text-2xl font-semibold">Tournament Platform</h1>
            </div>
            <div className="text-sm text-slate-400">
              Year-long multi-format tournament scaffolding with plug-in pairing and scoring.
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-12">{children}</main>
      </body>
    </html>
  );
}

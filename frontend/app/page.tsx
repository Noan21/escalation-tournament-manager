import Link from 'next/link';

const checklistItems = [
  {
    title: 'Stages & Formats',
    description:
      'Define sequences of Swiss, pods, or knockout stages per event. Each stage is powered by a dedicated pairing plugin.'
  },
  {
    title: 'Scoring Strategies',
    description:
      'Attach scoring profiles like Win/Draw/Loss or 20-0 spreads to a stage. Strategies compute match points and tie-breakers.'
  },
  {
    title: 'Workflow Agents',
    description:
      'Orchestrator, pairing, scoring, and notification agents expose asynchronous services triggered by API calls.'
  },
  {
    title: 'PostgreSQL Domain',
    description:
      'Normalized entities covering organizations, seasons, participants, teams, registrations, rounds, matches, and standings.'
  }
];

export default function HomePage() {
  return (
    <section className="space-y-12">
      <div className="space-y-6">
        <p className="text-lg text-slate-300">
          The Escalation Tournament Platform provides a neutral, extensible foundation for running year-long competitive
          programs across multiple event formats.
        </p>
        <p className="text-sm uppercase tracking-[0.3em] text-emerald-400">Platform Capabilities</p>
        <div className="grid gap-6 md:grid-cols-2">
          {checklistItems.map((item) => (
            <article key={item.title} className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 shadow-inner">
              <h2 className="text-xl font-medium text-white">{item.title}</h2>
              <p className="mt-2 text-sm text-slate-300">{item.description}</p>
            </article>
          ))}
        </div>
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-lg font-medium text-white">Get Started</h2>
        <p className="mt-2 text-sm text-slate-300">
          Spin up the Docker Compose stack to run the Next.js admin interface, FastAPI backend, and PostgreSQL database.
          Use the scaffolding to register organizations, configure seasons, and experiment with pairing + scoring plugins.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            href="https://fastapi.tiangolo.com"
            className="rounded-md bg-emerald-500 px-3 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400"
          >
            FastAPI Docs
          </Link>
          <Link
            href="https://nextjs.org/docs"
            className="rounded-md border border-emerald-500 px-3 py-2 text-sm font-semibold text-emerald-300 transition hover:border-emerald-300"
          >
            Next.js Guides
          </Link>
        </div>
      </div>
    </section>
  );
}

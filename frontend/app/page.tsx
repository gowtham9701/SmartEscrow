const metrics = [
  { label: 'Verified Talent', value: '87%' },
  { label: 'Escrow Release Time', value: '< 24h' },
  { label: 'Marketplace Fees', value: '0-3%' },
  { label: 'Dispute Resolution', value: '< 72h' },
];

const pillars = [
  {
    title: 'AI Technical Verification',
    desc: 'Repository-driven scoring from public code quality and delivery signals.',
  },
  {
    title: 'Fiat-Native Escrow',
    desc: 'USD milestone funding through Stripe sandbox rails with release on verified merge events.',
  },
  {
    title: 'Peer Arbitration',
    desc: 'Blind jury voting to resolve milestone disagreements without administrative delays.',
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.2em] text-sky-300">
          SmartEscrow
        </div>
        <h1 className="mt-8 max-w-4xl text-5xl font-semibold tracking-tight md:text-7xl">
          Algorithmic B2B infrastructure for elite tech talent.
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-slate-300">
          Replace resume greenwashing, slow disputes, and intermediary rent-seeking with a USD-native,
          AI-verified, milestone-based delivery network.
        </p>

        <div className="mt-10 flex flex-wrap gap-4">
          <a href="#platform" className="rounded-xl bg-sky-500 px-5 py-3 font-medium text-slate-950 transition hover:bg-sky-400">
            Explore platform
          </a>
          <a href="#business" className="rounded-xl border border-white/15 bg-white/5 px-5 py-3 font-medium text-white transition hover:bg-white/10">
            View business model
          </a>
        </div>

        <div className="mt-16 grid gap-4 md:grid-cols-4">
          {metrics.map((item) => (
            <div key={item.label} className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-lg shadow-sky-950/10">
              <div className="text-2xl font-semibold text-sky-300">{item.value}</div>
              <div className="mt-2 text-sm text-slate-300">{item.label}</div>
            </div>
          ))}
        </div>
      </section>

      <section id="platform" className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-8 text-3xl font-semibold">Why SmartEscrow</div>
        <div className="grid gap-6 md:grid-cols-3">
          {pillars.map((pillar) => (
            <div key={pillar.title} className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <div className="mb-4 h-10 w-10 rounded-full bg-sky-500/20" />
              <h3 className="text-xl font-semibold text-white">{pillar.title}</h3>
              <p className="mt-3 text-slate-300">{pillar.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="business" className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-3xl border border-sky-500/20 bg-gradient-to-br from-sky-950 to-slate-950 p-8 md:p-12">
          <div className="text-sm uppercase tracking-[0.2em] text-sky-300">Business model</div>
          <h2 className="mt-3 text-3xl font-semibold md:text-5xl">Low-margin operations, high-trust infrastructure.</h2>
          <p className="mt-5 max-w-3xl text-slate-200">
            SmartEscrow monetizes through enterprise SaaS, premium technical screening, and flat subscription tiers instead of prédatory percentage-based commission on worker earnings.
          </p>
        </div>
      </section>
    </main>
  );
}

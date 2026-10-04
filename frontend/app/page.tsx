import Link from 'next/link';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';
import { HomeStats } from '@/components/home-stats';

const SERVICES = [
  {
    tag: '01 — For Clients',
    title: 'Hire vetted talent',
    body: 'Search AI-graded engineers, designers, and specialists. Post a role, review ranked applicants, and start an hourly engagement in days — not weeks.',
    href: '/talent',
    cta: 'Browse Talent',
  },
  {
    tag: '02 — For Contributors',
    title: 'Find high-value work',
    body: 'Discover open roles that match your stack, set your own hourly rate, and apply with a portfolio that speaks louder than a résumé.',
    href: '/jobs',
    cta: 'Browse Jobs',
  },
  {
    tag: '03 — Built-In AI',
    title: 'Summarized & ranked',
    body: 'Every job post is auto-summarized with key points and a recommended skill profile, so both sides understand scope instantly.',
    href: '/how-it-works',
    cta: 'See How',
  },
];

const PILLARS = [
  { k: 'AI Technical Verification', v: 'Objective code-quality grading, not keyword-stuffed résumés.' },
  { k: 'Automated USD Escrow', v: 'Client cash is locked and released on verified delivery — fiat-native and compliant.' },
  { k: 'Peer Dispute Resolution', v: 'Blind, randomized senior-engineer juries resolve milestone conflicts fast.' },
  { k: 'Fiat-Staking Integrity', v: 'Refundable USD stakes eliminate spam, ghosting, and bad-faith contracts.' },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />

      {/* Hero */}
      <section className="container-x pt-14 pb-10 md:pt-20">
        <div className="mono-label">Algorithmic B2B Infrastructure for Tech Talent</div>
        <h1 className="display mt-6 text-[clamp(2.6rem,8vw,7rem)]">
          Talent,
          <br />
          reimagined.
        </h1>
        <div className="mt-10 grid gap-10 md:grid-cols-[1.4fr_1fr] md:items-end">
          <p className="max-w-xl font-mono text-sm leading-relaxed text-ink/70">
            SmartEscrow connects elite engineering talent with the companies that need them —
            through AI vetting, transparent hourly rates, and automated USD escrow that pays on
            verified delivery. Zero predatory commissions.
          </p>
          <div className="flex flex-wrap gap-3 md:justify-end">
            <Link href="/register?role=client" className="btn-navy">
              Hire Talent
            </Link>
            <Link href="/register?role=contributor" className="btn-outline">
              Find Work
            </Link>
          </div>
        </div>
      </section>

      {/* Hero band */}
      <section className="container-x">
        <div className="relative overflow-hidden rounded-3xl border border-ink/10">
          <div className="grid gap-0 md:grid-cols-3">
            <div className="bg-navy p-10 text-paper">
              <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-paper/60">
                Fiat-native
              </div>
              <div className="mt-6 font-display text-4xl font-bold">0%</div>
              <p className="mt-2 text-sm text-paper/70">
                predatory rent-seeking commission on worker earnings.
              </p>
            </div>
            <div className="bg-coal p-10 text-paper">
              <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-paper/60">
                Verified delivery
              </div>
              <div className="mt-6 font-display text-4xl font-bold">&lt; 24h</div>
              <p className="mt-2 text-sm text-paper/70">
                target payout latency after an approved merge event.
              </p>
            </div>
            <div className="bg-accent p-10 text-paper">
              <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-white/70">
                Objective vetting
              </div>
              <div className="mt-6 font-display text-4xl font-bold">AI</div>
              <p className="mt-2 text-sm text-white/80">
                code-quality grading replaces résumé greenwashing.
              </p>
            </div>
          </div>
        </div>
      </section>

      <HomeStats />

      {/* Services */}
      <section className="container-x mt-10">
        <div className="flex items-end justify-between">
          <h2 className="display text-[clamp(2rem,5vw,4rem)]">What we do</h2>
          <div className="mono-label hidden md:block">Two sides. One protocol.</div>
        </div>
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {SERVICES.map((s) => (
            <Link
              key={s.title}
              href={s.href}
              className="card group flex flex-col p-8 transition hover:-translate-y-1 hover:shadow-xl"
            >
              <div className="mono-label text-accent">{s.tag}</div>
              <h3 className="mt-5 font-display text-2xl font-bold tracking-tight">
                {s.title}
              </h3>
              <p className="mt-4 flex-1 text-sm leading-relaxed text-ink/70">{s.body}</p>
              <span className="mt-6 inline-flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-navy">
                {s.cta}
                <span className="transition group-hover:translate-x-1">→</span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Pillars */}
      <section className="container-x mt-24">
        <div className="mono-label text-accent">The SmartEscrow Architecture</div>
        <h2 className="display mt-5 max-w-4xl text-[clamp(1.8rem,4.5vw,3.4rem)]">
          Four pillars that replace human admin with software logic.
        </h2>
        <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-ink/10 bg-ink/10 md:grid-cols-2">
          {PILLARS.map((p, i) => (
            <div key={p.k} className="bg-bone p-8">
              <div className="font-display text-5xl font-bold text-ink/15">0{i + 1}</div>
              <div className="mt-4 font-display text-xl font-bold tracking-tight">
                {p.k}
              </div>
              <p className="mt-2 text-sm text-ink/70">{p.v}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="container-x mt-24">
        <div className="rounded-3xl bg-navy px-8 py-16 text-paper md:px-16 md:py-24">
          <div className="mono-label text-paper/60">Ready when you are</div>
          <h2 className="display mt-6 text-[clamp(2.2rem,6vw,5rem)]">
            Let&apos;s build
            <br />
            your team.
          </h2>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link href="/register?role=client" className="btn-ink bg-paper text-coal hover:bg-paper/90">
              Post a Job
            </Link>
            <Link
              href="/register?role=contributor"
              className="btn-outline border-paper/40 text-paper hover:bg-paper hover:text-coal"
            >
              Join as Talent
            </Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

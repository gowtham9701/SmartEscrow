import Link from 'next/link';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';

const PROBLEMS = [
  { k: 'Predatory Commissions', v: 'Legacy networks skim up to 20% from workers and tack on client-side fees — suppressing wages and inflating budgets.' },
  { k: 'Résumé Greenwashing', v: 'Keyword-stuffed résumés drive mismatches, hidden tech-debt, and costly hiring failures.' },
  { k: 'Slow, Biased Disputes', v: 'Non-technical admins resolve conflicts over weeks, choking cash flow for independents and agencies.' },
  { k: 'Cross-Border Friction', v: 'Legacy wires add hidden intermediary fees and clearing latency to every international payout.' },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />
      <section className="container-x pt-16 pb-10">
        <div className="mono-label text-accent">About SmartEscrow</div>
        <h1 className="display mt-6 max-w-5xl text-[clamp(2.2rem,5.5vw,4.8rem)]">
          We fixed the broken middle of tech hiring.
        </h1>
        <p className="mt-8 max-w-2xl font-mono text-sm leading-relaxed text-ink/70">
          SmartEscrow is a low-margin, highly automated B2B platform engineered for elite software
          talent. We replace human administrative layers with programmatic logic — so clients hire
          faster, contributors keep more, and every dollar moves on verified delivery.
        </p>
      </section>

      <section className="container-x mt-10">
        <div className="mono-label">The Market Friction We Remove</div>
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          {PROBLEMS.map((p) => (
            <div key={p.k} className="card p-8">
              <div className="font-display text-xl font-bold tracking-tight">{p.k}</div>
              <p className="mt-3 text-sm text-ink/70">{p.v}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container-x mt-20">
        <div className="grid gap-6 md:grid-cols-3">
          {[
            { k: 'Mission', v: 'Make elite engineering work accessible, fairly paid, and objectively verified.' },
            { k: 'Model', v: 'Fiat-native USD escrow with full corporate and banking compliance, built for regulated enterprise engagements.' },
            { k: 'Method', v: 'AI vetting, automated escrow, and peer juries running on open-source, zero-cost infrastructure.' },
          ].map((c) => (
            <div key={c.k} className="rounded-2xl bg-navy p-8 text-paper">
              <div className="mono-label text-paper/60">{c.k}</div>
              <p className="mt-4 text-lg">{c.v}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container-x mt-20">
        <div className="rounded-3xl bg-coal px-8 py-16 text-paper md:px-16">
          <h2 className="display text-[clamp(1.8rem,5vw,3.5rem)]">Join the platform.</h2>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link href="/register" className="btn-ink bg-paper text-coal hover:bg-paper/90">Get Started</Link>
            <Link href="/contact" className="btn-outline border-paper/40 text-paper hover:bg-paper hover:text-coal">Contact Us</Link>
          </div>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}

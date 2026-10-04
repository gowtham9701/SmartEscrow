import Link from 'next/link';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';

const STEPS = [
  {
    n: '01',
    title: 'Post or Discover',
    client: 'Clients post a role with scope, skills, and an hourly budget. Our AI instantly summarizes it into key points.',
    talent: 'Contributors browse open roles ranked by match score and apply with a preferred hourly rate.',
  },
  {
    n: '02',
    title: 'AI Vetting & Ranking',
    client: 'Applicants are ranked by objective skill-match and portfolio signal — no résumé greenwashing.',
    talent: 'Your public work and skills generate an objective talent profile that clients can trust.',
  },
  {
    n: '03',
    title: 'Hourly Engagement',
    client: 'Hire with one click. Fund an escrow vault in strict USD and track logged hours in real time.',
    talent: 'Log your hours against the engagement. Every timesheet creates a transparent escrow record.',
  },
  {
    n: '04',
    title: 'Verified Payout',
    client: 'Release escrow on verified delivery. Disputes go to a blind senior-engineer jury.',
    talent: 'Get paid fast on approved work — with zero predatory commission skimmed off the top.',
  },
];

export default function HowItWorksPage() {
  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />
      <section className="container-x pt-16 pb-10">
        <div className="mono-label text-accent">The Protocol</div>
        <h1 className="display mt-6 text-[clamp(2.4rem,7vw,6rem)]">How it works</h1>
        <p className="mt-6 max-w-2xl font-mono text-sm leading-relaxed text-ink/70">
          SmartEscrow strips away human administrative layers and replaces them with programmatic
          software logic — AI vetting, automated USD escrow, and peer-led dispute resolution.
        </p>
      </section>

      <section className="container-x">
        <div className="grid gap-px overflow-hidden rounded-2xl border border-ink/10 bg-ink/10">
          {STEPS.map((s) => (
            <div key={s.n} className="grid gap-6 bg-bone p-8 md:grid-cols-[120px_1fr_1fr] md:p-10">
              <div className="font-display text-6xl font-bold text-ink/15">{s.n}</div>
              <div>
                <div className="font-display text-2xl font-bold tracking-tight">{s.title}</div>
                <div className="mono-label mt-4 text-navy">For Clients</div>
                <p className="mt-1 text-sm text-ink/70">{s.client}</p>
              </div>
              <div className="md:pt-16">
                <div className="mono-label text-accent">For Contributors</div>
                <p className="mt-1 text-sm text-ink/70">{s.talent}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="container-x mt-20">
        <div className="rounded-3xl bg-coal px-8 py-16 text-paper md:px-16">
          <h2 className="display text-[clamp(1.8rem,5vw,3.5rem)]">Start in minutes.</h2>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link href="/register?role=client" className="btn-ink bg-paper text-ink hover:bg-paper/90">Hire Talent</Link>
            <Link href="/register?role=contributor" className="btn-outline border-paper/40 text-paper hover:bg-paper hover:text-ink">Find Work</Link>
          </div>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}

'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';
import { LIFECYCLE_STAGES } from '@/components/lifecycle/lifecycle-visualizer';

// R3F renders with WebGL and cannot be server-rendered.
const LifecycleVisualizer = dynamic(
  () => import('@/components/lifecycle/lifecycle-visualizer').then((m) => m.LifecycleVisualizer),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[420px] items-center justify-center rounded-2xl border border-ink/10 bg-coal">
        <span className="font-mono text-sm text-paper/60">Loading 3D scene…</span>
      </div>
    ),
  },
);

export default function LifecyclePage() {
  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />

      <section className="container-x pt-16 pb-10">
        <div className="mono-label text-accent">Contract Lifecycle</div>
        <h1 className="display mt-6 text-[clamp(2.4rem,7vw,6rem)]">
          Watch a contract come to life
        </h1>
        <p className="mt-6 max-w-2xl font-mono text-sm leading-relaxed text-ink/70">
          Every SmartEscrow engagement moves through four programmatic stages. The
          escrowed USD is blocked the moment a milestone locks, and released
          automatically once delivery is verified — no human middleman.
        </p>
      </section>

      <section className="container-x">
        <LifecycleVisualizer />
      </section>

      <section className="container-x mt-16">
        <div className="grid gap-px overflow-hidden rounded-2xl border border-ink/10 bg-ink/10 md:grid-cols-4">
          {LIFECYCLE_STAGES.map((s, i) => (
            <div key={s.key} className="bg-bone p-8">
              <div className="font-display text-5xl font-bold text-ink/15">{`0${i + 1}`}</div>
              <div className="mt-4 font-display text-xl font-bold tracking-tight">{s.label}</div>
              <p className="mt-2 text-sm text-ink/70">{s.blurb}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container-x my-20">
        <div className="rounded-3xl bg-coal px-8 py-16 text-paper md:px-16">
          <h2 className="display text-[clamp(1.8rem,5vw,3.5rem)]">Fund a milestone in minutes.</h2>
          <p className="mt-4 max-w-xl font-mono text-sm text-paper/70">
            Create an engagement, block USD into escrow, and release on verified
            delivery — all from your dashboard.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link href="/register?role=client" className="btn-ink bg-paper text-coal hover:bg-paper/90">
              Hire Talent
            </Link>
            <Link href="/dashboard" className="btn-outline border-paper/40 text-paper hover:bg-paper hover:text-coal">
              Go to Dashboard
            </Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

'use client';

import { useState } from 'react';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';

export default function ContactPage() {
  const [sent, setSent] = useState(false);

  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />
      <section className="container-x grid gap-12 pt-16 pb-10 md:grid-cols-[1.1fr_1fr]">
        <div>
          <div className="mono-label text-accent">Contact</div>
          <h1 className="display mt-6 text-[clamp(2.2rem,5.5vw,4.5rem)]">
            Let&apos;s pioneer your next breakthrough.
          </h1>
          <p className="mt-8 max-w-md font-mono text-sm leading-relaxed text-ink/70">
            Ready to reimagine what&apos;s possible? Share a few details below, and together we&apos;ll
            map the future of your engineering delivery.
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            setSent(true);
          }}
          className="card p-8"
        >
          {sent ? (
            <div className="flex h-full flex-col items-center justify-center py-12 text-center">
              <div className="font-display text-2xl font-bold tracking-tight">Message sent.</div>
              <p className="mt-2 text-sm text-ink/60">We&apos;ll be in touch shortly.</p>
            </div>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <Field label="First Name" />
                <Field label="Last Name" />
              </div>
              <div className="mt-4">
                <Field label="Email" type="email" />
              </div>
              <div className="mt-4">
                <label className="mono-label mb-2 block">Message</label>
                <textarea className="input min-h-[140px]" placeholder="Tell us about your needs…" />
              </div>
              <button type="submit" className="btn-navy mt-6 w-full">Submit</button>
            </>
          )}
        </form>
      </section>
      <SiteFooter />
    </div>
  );
}

function Field({ label, type = 'text' }: { label: string; type?: string }) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <input type={type} className="input" />
    </label>
  );
}

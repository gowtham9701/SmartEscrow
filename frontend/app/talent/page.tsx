'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';
import { Avatar, SkillChips, Stars, EmptyState } from '@/components/ui';
import { api } from '@/lib/api';
import type { User } from '@/lib/types';

export default function TalentPage() {
  const [talent, setTalent] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.listTalent({ search });
      setTalent(res.talent);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />

      <section className="container-x pt-14 pb-6">
        <div className="mono-label text-accent">For Clients</div>
        <h1 className="display mt-4 text-[clamp(2.2rem,6vw,5rem)]">Find talent</h1>
        <p className="mt-4 max-w-xl font-mono text-sm text-ink/60">
          Browse AI-vetted contributors. Every profile shows objective skills, portfolio, and a
          transparent hourly rate.
        </p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            load();
          }}
          className="mt-8 flex flex-col gap-3 md:flex-row"
        >
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, title, or skill…"
            className="input md:flex-1"
          />
          <button type="submit" className="btn-ink">Search</button>
        </form>
      </section>

      <section className="container-x pb-10">
        {loading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-72 animate-pulse rounded-2xl bg-ink/5" />
            ))}
          </div>
        ) : talent.length === 0 ? (
          <EmptyState title="No talent found" body="Try a broader search term." />
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {talent.map((t) => (
              <Link
                key={t.id}
                href={`/talent/${t.id}`}
                className="card group flex flex-col p-6 transition hover:-translate-y-1 hover:shadow-xl"
              >
                <div className="flex items-start gap-4">
                  <Avatar name={t.full_name} hue={t.avatar_hue} size={56} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-display text-lg font-bold tracking-tight">
                      {t.full_name}
                    </div>
                    <div className="truncate font-mono text-xs text-ink/50">{t.title}</div>
                    <div className="mt-1 flex items-center gap-2">
                      {typeof t.rating === 'number' && <Stars rating={t.rating} />}
                      <span className="font-mono text-[11px] text-ink/40">· {t.location}</span>
                    </div>
                  </div>
                </div>

                <p className="mt-4 line-clamp-2 flex-1 text-sm text-ink/70">{t.bio}</p>

                <div className="mt-4">
                  <SkillChips skills={t.skills || []} max={4} />
                </div>

                <div className="mt-5 flex items-center justify-between border-t border-ink/10 pt-4">
                  <div className="font-display text-lg font-bold">
                    ${t.hourly_rate_usd}
                    <span className="font-sans text-xs font-normal text-ink/50">/hr</span>
                  </div>
                  <div className="font-mono text-[11px] text-ink/50">
                    {t.years_experience}y exp · {t.completed_jobs} jobs
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <SiteFooter />
    </div>
  );
}

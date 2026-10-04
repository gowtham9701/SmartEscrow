'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';
import { Avatar, SkillChips, Stars } from '@/components/ui';
import { api } from '@/lib/api';
import type { User } from '@/lib/types';

export default function TalentProfilePage() {
  const { id } = useParams<{ id: string }>();
  const [t, setT] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    api
      .getTalent(id)
      .then(setT)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-bone">
        <SiteHeader />
        <div className="container-x py-20">
          <div className="h-40 animate-pulse rounded-2xl bg-ink/5" />
        </div>
      </div>
    );
  }

  if (notFound || !t) {
    return (
      <div className="min-h-screen bg-bone">
        <SiteHeader />
        <div className="container-x py-20 text-center">
          <h1 className="display text-3xl">Profile not found</h1>
          <Link href="/talent" className="btn-navy mt-6">Back to talent</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />

      <section className="container-x pt-10">
        <Link href="/talent" className="font-mono text-xs uppercase tracking-wide text-ink/50 hover:text-navy">
          ← All talent
        </Link>
      </section>

      <section className="container-x mt-6 grid gap-8 lg:grid-cols-[1.6fr_1fr]">
        <div>
          <div className="card p-8">
            <div className="flex flex-wrap items-start gap-6">
              <Avatar name={t.full_name} hue={t.avatar_hue} size={88} />
              <div className="min-w-0 flex-1">
                <h1 className="font-display text-3xl font-bold tracking-tight">{t.full_name}</h1>
                <div className="mt-1 font-mono text-sm text-ink/60">{t.title}</div>
                <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-ink/50">
                  {typeof t.rating === 'number' && <Stars rating={t.rating} />}
                  <span className="font-mono text-xs">· {t.location}</span>
                  <span className="font-mono text-xs">· {t.years_experience}y experience</span>
                  <span className="font-mono text-xs">· {t.completed_jobs} jobs completed</span>
                </div>
              </div>
            </div>
            <p className="mt-6 text-sm leading-relaxed text-ink/80">{t.bio}</p>
            <div className="mt-6">
              <div className="mono-label">Skills</div>
              <div className="mt-3">
                <SkillChips skills={t.skills || []} max={30} />
              </div>
            </div>
          </div>

          {t.experiences && t.experiences.length > 0 && (
            <div className="mt-8">
              <div className="mono-label text-accent">Experience</div>
              <div className="mt-4 space-y-4">
                {t.experiences.map((e, i) => (
                  <div key={i} className="card p-6">
                    <div className="flex items-baseline justify-between gap-4">
                      <div className="font-display text-lg font-bold tracking-tight">{e.role}</div>
                      <div className="font-mono text-xs text-ink/50">{e.period}</div>
                    </div>
                    <div className="font-mono text-xs text-navy">{e.company}</div>
                    <p className="mt-2 text-sm text-ink/70">{e.summary}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {t.portfolio && t.portfolio.length > 0 && (
            <div className="mt-8">
              <div className="mono-label text-accent">Portfolio</div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {t.portfolio.map((p, i) => (
                  <a key={i} href={p.url || '#'} target="_blank" rel="noreferrer" className="card p-5 transition hover:shadow-lg">
                    <div className="font-display text-base font-bold tracking-tight">{p.title}</div>
                    <p className="mt-1 text-sm text-ink/60">{p.summary}</p>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="card p-6">
            <div className="font-display text-3xl font-bold">
              ${t.hourly_rate_usd}
              <span className="font-sans text-sm font-normal text-ink/50">/hr</span>
            </div>
            <div className="mono-label mt-1">base rate · {t.availability}</div>
            <Link href="/jobs/new" className="btn-navy mt-6 w-full">Invite to a Role</Link>
            <p className="mt-3 text-center font-mono text-[10px] text-ink/50">
              Post a job to start an engagement with this contributor.
            </p>
          </div>

          {t.services && t.services.length > 0 && (
            <div className="card mt-6 p-6">
              <div className="mono-label">Service Rates</div>
              <div className="mt-4 space-y-3">
                {t.services.map((s, i) => (
                  <div key={i} className="flex items-center justify-between border-b border-ink/5 pb-2 text-sm">
                    <span className="text-ink/75">{s.title}</span>
                    <span className="font-display font-bold">${s.rate}/hr</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {t.achievements && t.achievements.length > 0 && (
            <div className="card mt-6 p-6">
              <div className="mono-label">Achievements</div>
              <ul className="mt-4 space-y-2 text-sm text-ink/75">
                {t.achievements.map((a, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-accent">★</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {t.github_username && (
            <div className="card mt-6 p-6">
              <div className="mono-label">Verified Repository</div>
              <a
                href={`https://github.com/${t.github_username}`}
                target="_blank"
                rel="noreferrer"
                className="mt-2 block font-mono text-sm text-navy hover:underline"
              >
                github.com/{t.github_username}
              </a>
            </div>
          )}
        </aside>
      </section>

      <SiteFooter />
    </div>
  );
}

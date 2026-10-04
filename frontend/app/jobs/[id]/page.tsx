'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';
import { Avatar, SkillChips, Stars, MatchBadge } from '@/components/ui';
import { api, timeAgo } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { Job } from '@/lib/types';

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [rate, setRate] = useState(90);
  const [cover, setCover] = useState('');
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .getJob(id)
      .then((j) => {
        setJob(j);
        setRate(Math.round((j.hourly_rate_min + j.hourly_rate_max) / 2));
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);

  const apply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      router.push('/login');
      return;
    }
    setApplying(true);
    setError('');
    try {
      await api.apply(id, { proposed_hourly_rate: rate, cover_letter: cover });
      setApplied(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply');
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bone">
        <SiteHeader />
        <div className="container-x py-20">
          <div className="h-10 w-2/3 animate-pulse rounded bg-ink/10" />
          <div className="mt-6 h-40 animate-pulse rounded-2xl bg-ink/5" />
        </div>
      </div>
    );
  }

  if (notFound || !job) {
    return (
      <div className="min-h-screen bg-bone">
        <SiteHeader />
        <div className="container-x py-20 text-center">
          <h1 className="display text-3xl">Job not found</h1>
          <Link href="/jobs" className="btn-navy mt-6">Back to jobs</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />

      <section className="container-x pt-10">
        <Link href="/jobs" className="font-mono text-xs uppercase tracking-wide text-ink/50 hover:text-navy">
          ← All roles
        </Link>
        <div className="mt-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mono-label text-accent">{job.category}</div>
            <h1 className="display mt-3 max-w-3xl text-[clamp(1.8rem,4.5vw,3.5rem)]">{job.title}</h1>
            <div className="mt-3 font-mono text-sm text-ink/60">
              {job.company_name} · {job.location} · Posted {timeAgo(job.created_at)}
            </div>
          </div>
          <div className="text-right">
            <div className="font-display text-3xl font-bold">
              ${job.hourly_rate_min}–${job.hourly_rate_max}
            </div>
            <div className="mono-label">per hour</div>
          </div>
        </div>
      </section>

      <section className="container-x mt-10 grid gap-8 lg:grid-cols-[1.6fr_1fr]">
        <div>
          {/* AI brief */}
          <div className="card overflow-hidden">
            <div className="flex items-center gap-2 border-b border-ink/10 bg-navy px-6 py-3 text-paper">
              <span className="font-mono text-[11px] uppercase tracking-[0.18em]">✦ AI Summary</span>
              <span className="ml-auto font-mono text-[10px] text-paper/60">
                ~{job.ai.reading_time_sec}s read · {job.ai.suggested_seniority}
              </span>
            </div>
            <div className="p-6">
              <p className="text-sm leading-relaxed text-ink/80">{job.ai.summary}</p>
              <div className="mono-label mt-6 text-accent">Key Points</div>
              <ul className="mt-3 space-y-2">
                {job.ai.key_points.map((kp, i) => (
                  <li key={i} className="flex gap-3 text-sm text-ink/75">
                    <span className="font-mono text-accent">0{i + 1}</span>
                    {kp}
                  </li>
                ))}
              </ul>
              <div className="mono-label mt-6 text-accent">Recommended Skill Profile</div>
              <div className="mt-3">
                <SkillChips skills={job.ai.recommended_skills} max={10} />
              </div>
              <div className="mt-6 rounded-xl bg-ink/5 p-4 text-sm italic text-ink/70">
                {job.ai.recommendation}
              </div>
            </div>
          </div>

          {/* Full description */}
          <div className="mt-8">
            <div className="mono-label">Full Description</div>
            <p className="mt-4 whitespace-pre-line text-sm leading-relaxed text-ink/80">
              {job.description}
            </p>
            <div className="mt-6">
              <div className="mono-label">Required Skills</div>
              <div className="mt-3">
                <SkillChips skills={job.skills_required} max={20} />
              </div>
            </div>
          </div>

          {/* Recommended talent */}
          {job.recommended_talent && job.recommended_talent.length > 0 && (
            <div className="mt-12">
              <div className="mono-label text-accent">AI-Matched Talent</div>
              <h2 className="display mt-3 text-2xl">Top candidates</h2>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {job.recommended_talent.map((t) => (
                  <Link key={t.id} href={`/talent/${t.id}`} className="card flex items-center gap-4 p-4 transition hover:shadow-lg">
                    <Avatar name={t.full_name} hue={t.avatar_hue} />
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-semibold">{t.full_name}</div>
                      <div className="truncate font-mono text-xs text-ink/50">{t.title}</div>
                    </div>
                    {typeof t.match_score === 'number' && <MatchBadge score={t.match_score} />}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Apply panel */}
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="card p-6">
            <div className="font-display text-lg font-bold tracking-tight">Apply Now</div>
            <div className="mt-1 font-mono text-xs text-ink/50">
              {job.applicant_count || 0} applicant{job.applicant_count === 1 ? '' : 's'} so far
            </div>

            {applied ? (
              <div className="mt-6 rounded-xl border border-emerald-300 bg-emerald-50 p-4 text-center">
                <div className="font-display text-lg font-bold tracking-tight text-emerald-800">Applied!</div>
                <p className="mt-1 text-sm text-emerald-700">Track it from your dashboard.</p>
                <Link href="/dashboard" className="btn-navy mt-4 w-full">Go to Dashboard</Link>
              </div>
            ) : user?.role === 'client' ? (
              <p className="mt-6 text-sm text-ink/60">
                You&apos;re signed in as a client. Switch to a contributor account to apply.
              </p>
            ) : (
              <form onSubmit={apply} className="mt-6 space-y-4">
                <label className="block">
                  <span className="mono-label mb-2 block">Your Hourly Rate (USD)</span>
                  <input
                    type="number"
                    min={5}
                    value={rate}
                    onChange={(e) => setRate(Number(e.target.value))}
                    className="input"
                  />
                </label>
                <label className="block">
                  <span className="mono-label mb-2 block">Cover Note</span>
                  <textarea
                    value={cover}
                    onChange={(e) => setCover(e.target.value)}
                    placeholder="Why you're a great fit…"
                    className="input min-h-[120px]"
                  />
                </label>
                {error && (
                  <div className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>
                )}
                <button type="submit" disabled={applying} className="btn-navy w-full disabled:opacity-60">
                  {applying ? 'Submitting…' : user ? 'Submit Application' : 'Sign in to Apply'}
                </button>
                {!user && (
                  <p className="text-center font-mono text-[10px] text-ink/50">You&apos;ll be asked to sign in first.</p>
                )}
              </form>
            )}
          </div>

          <div className="card mt-6 p-6">
            <div className="mono-label">Engagement Details</div>
            <dl className="mt-4 space-y-3 text-sm">
              <Row k="Type" v={job.engagement_type} />
              <Row k="Experience" v={job.experience_level} />
              <Row k="Commitment" v={`${job.hours_per_week}h / week`} />
              <Row k="Duration" v={job.duration} />
              <Row k="Location" v={job.location} />
            </dl>
          </div>
        </aside>
      </section>

      <SiteFooter />
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between border-b border-ink/5 pb-2">
      <dt className="font-mono text-xs uppercase tracking-wide text-ink/50">{k}</dt>
      <dd className="font-medium capitalize">{v}</dd>
    </div>
  );
}

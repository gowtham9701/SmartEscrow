'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';
import { SkillChips } from '@/components/ui';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { JobAI } from '@/lib/types';

const CATEGORIES = ['Backend', 'Frontend', 'AI / ML', 'Design', 'DevOps', 'Security', 'Mobile', 'Data'];
const LEVELS = ['Junior', 'Mid-level', 'Senior', 'Lead'];

export default function NewJobPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Backend');
  const [description, setDescription] = useState('');
  const [skills, setSkills] = useState('');
  const [rateMin, setRateMin] = useState(50);
  const [rateMax, setRateMax] = useState(90);
  const [level, setLevel] = useState('Senior');
  const [hours, setHours] = useState(30);
  const [duration, setDuration] = useState('3-6 months');

  const [ai, setAi] = useState<JobAI | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!loading && (!user || user.role !== 'client')) {
      router.push('/login');
    }
  }, [user, loading, router]);

  // Live AI preview (debounced).
  useEffect(() => {
    if (description.trim().length < 20) {
      setAi(null);
      return;
    }
    const t = setTimeout(() => {
      api.summarize(title, description).then(setAi).catch(() => setAi(null));
    }, 600);
    return () => clearTimeout(t);
  }, [title, description]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const job = await api.createJob({
        title,
        category,
        description,
        skills_required: skills.split(',').map((s) => s.trim()).filter(Boolean),
        hourly_rate_min: rateMin,
        hourly_rate_max: rateMax,
        experience_level: level,
        hours_per_week: hours,
        duration,
      });
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job');
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />
      <section className="container-x pt-12 pb-6">
        <div className="mono-label text-accent">For Clients</div>
        <h1 className="display mt-4 text-[clamp(2rem,5vw,4rem)]">Post a job</h1>
        <p className="mt-4 max-w-xl font-mono text-sm text-ink/60">
          Describe the role. Our AI summarizes it live so contributors instantly understand scope.
        </p>
      </section>

      <section className="container-x grid gap-8 pb-10 lg:grid-cols-[1.4fr_1fr]">
        <form onSubmit={submit} className="card space-y-5 p-8">
          <Field label="Job Title" value={title} onChange={setTitle} required placeholder="e.g. Senior Backend Engineer — Payments" />

          <div className="grid gap-4 sm:grid-cols-2">
            <Select label="Category" value={category} onChange={setCategory} options={CATEGORIES} />
            <Select label="Experience Level" value={level} onChange={setLevel} options={LEVELS} />
          </div>

          <label className="block">
            <span className="mono-label mb-2 block">Description</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              placeholder="Describe responsibilities, requirements, and what success looks like…"
              className="input min-h-[200px]"
            />
          </label>

          <Field label="Required Skills (comma-separated)" value={skills} onChange={setSkills} placeholder="Python, FastAPI, PostgreSQL" />

          <div className="grid gap-4 sm:grid-cols-3">
            <NumberField label="Rate Min ($/hr)" value={rateMin} onChange={setRateMin} />
            <NumberField label="Rate Max ($/hr)" value={rateMax} onChange={setRateMax} />
            <NumberField label="Hours / week" value={hours} onChange={setHours} />
          </div>

          <Field label="Duration" value={duration} onChange={setDuration} placeholder="3-6 months" />

          {error && (
            <div className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>
          )}

          <button type="submit" disabled={submitting} className="btn-navy w-full disabled:opacity-60">
            {submitting ? 'Publishing…' : 'Publish Job'}
          </button>
        </form>

        {/* Live AI preview */}
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="card overflow-hidden">
            <div className="flex items-center gap-2 bg-navy px-6 py-3 text-paper">
              <span className="font-mono text-[11px] uppercase tracking-[0.18em]">✦ Live AI Preview</span>
            </div>
            <div className="p-6">
              {ai ? (
                <>
                  <p className="text-sm leading-relaxed text-ink/80">{ai.summary}</p>
                  <div className="mono-label mt-5 text-accent">Key Points</div>
                  <ul className="mt-2 space-y-1.5">
                    {ai.key_points.map((kp, i) => (
                      <li key={i} className="text-sm text-ink/70">— {kp}</li>
                    ))}
                  </ul>
                  <div className="mono-label mt-5 text-accent">Detected Skills</div>
                  <div className="mt-2">
                    <SkillChips skills={ai.recommended_skills} max={10} />
                  </div>
                  <div className="mt-4 font-mono text-[11px] text-ink/50">
                    Suggested seniority: {ai.suggested_seniority}
                  </div>
                </>
              ) : (
                <p className="font-mono text-sm text-ink/40">
                  Start typing a description (20+ characters) to see the AI summary appear here.
                </p>
              )}
            </div>
          </div>
        </aside>
      </section>
      <SiteFooter />
    </div>
  );
}

function Field({ label, value, onChange, required, placeholder }: { label: string; value: string; onChange: (v: string) => void; required?: boolean; placeholder?: string }) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} required={required} placeholder={placeholder} className="input" />
    </label>
  );
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} className="input" />
    </label>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="input">
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </label>
  );
}

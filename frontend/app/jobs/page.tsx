'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';
import { JobCard } from '@/components/job-card';
import { EmptyState } from '@/components/ui';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { Job } from '@/lib/types';

const CATEGORIES = ['All', 'Backend', 'Frontend', 'AI / ML', 'Design', 'DevOps', 'Security'];

export default function JobsPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.listJobs({
        search,
        category: category === 'All' ? '' : category,
      });
      setJobs(res.jobs);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category]);

  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />

      <section className="container-x pt-14 pb-6">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <div className="mono-label text-accent">For Contributors</div>
            <h1 className="display mt-4 text-[clamp(2.2rem,6vw,5rem)]">Find work</h1>
          </div>
          {user?.role === 'client' && (
            <Link href="/jobs/new" className="btn-navy">
              + Post a Job
            </Link>
          )}
        </div>

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
            placeholder="Search roles, skills, companies…"
            className="input md:flex-1"
          />
          <button type="submit" className="btn-ink">
            Search
          </button>
        </form>

        <div className="mt-6 flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`rounded-full px-4 py-2 font-mono text-[11px] uppercase tracking-wide transition ${
                category === c ? 'bg-navy text-paper' : 'border border-ink/15 bg-surface text-ink/60 hover:border-ink'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </section>

      <section className="container-x pb-10">
        {loading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-60 animate-pulse rounded-2xl bg-ink/5" />
            ))}
          </div>
        ) : jobs.length === 0 ? (
          <EmptyState title="No roles found" body="Try a different search or category filter." />
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </section>

      <SiteFooter />
    </div>
  );
}

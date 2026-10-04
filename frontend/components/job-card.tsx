import Link from 'next/link';
import type { Job } from '@/lib/types';
import { timeAgo } from '@/lib/api';
import { MatchBadge, SkillChips } from './ui';

export function JobCard({ job }: { job: Job }) {
  return (
    <Link
      href={`/jobs/${job.id}`}
      className="card group flex flex-col p-6 transition hover:-translate-y-1 hover:shadow-xl"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="mono-label text-accent">{job.category}</div>
          <h3 className="mt-2 font-display text-xl font-bold leading-tight tracking-tight">
            {job.title}
          </h3>
          <div className="mt-1 font-mono text-xs text-ink/50">{job.company_name}</div>
        </div>
        {typeof job.match_score === 'number' && <MatchBadge score={job.match_score} />}
      </div>

      <p className="mt-4 line-clamp-2 flex-1 text-sm text-ink/70">
        {job.ai?.summary || job.description}
      </p>

      <div className="mt-5">
        <SkillChips skills={job.skills_required} max={4} />
      </div>

      <div className="mt-5 flex items-center justify-between border-t border-ink/10 pt-4">
        <div className="font-display text-lg font-bold">
          ${job.hourly_rate_min}–${job.hourly_rate_max}
          <span className="font-sans text-xs font-normal text-ink/50">/hr</span>
        </div>
        <div className="font-mono text-[11px] text-ink/50">
          {job.experience_level} · {job.hours_per_week}h/wk · {timeAgo(job.created_at)}
        </div>
      </div>
    </Link>
  );
}

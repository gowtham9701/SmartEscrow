import type { ReactNode } from 'react';

export function Avatar({ name, hue = 210, size = 48 }: { name: string; hue?: number; size?: number }) {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full font-display font-bold text-white"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.36,
        background: `linear-gradient(135deg, hsl(${hue} 45% 32%), hsl(${(hue + 40) % 360} 50% 42%))`,
      }}
    >
      {initials}
    </div>
  );
}

const STATUS_STYLES: Record<string, string> = {
  submitted: 'bg-ink/10 text-ink/70',
  shortlisted: 'bg-blue-100 dark:bg-blue-500/25 text-blue-800 dark:text-blue-200',
  interview: 'bg-amber-100 dark:bg-amber-500/25 text-amber-800 dark:text-amber-200',
  offer: 'bg-violet-100 dark:bg-violet-500/25 text-violet-800 dark:text-violet-200',
  hired: 'bg-emerald-100 dark:bg-emerald-500/25 text-emerald-800 dark:text-emerald-200',
  rejected: 'bg-rose-100 dark:bg-rose-500/25 text-rose-700 dark:text-rose-200',
  active: 'bg-emerald-100 dark:bg-emerald-500/25 text-emerald-800 dark:text-emerald-200',
  paused: 'bg-amber-100 dark:bg-amber-500/25 text-amber-800 dark:text-amber-200',
  completed: 'bg-emerald-100 dark:bg-emerald-500/25 text-emerald-800 dark:text-emerald-200',
  in_escrow: 'bg-amber-100 dark:bg-amber-500/25 text-amber-800 dark:text-amber-200',
  funded: 'bg-blue-100 dark:bg-blue-500/25 text-blue-800 dark:text-blue-200',
  released: 'bg-emerald-100 dark:bg-emerald-500/25 text-emerald-800 dark:text-emerald-200',
  open: 'bg-emerald-100 dark:bg-emerald-500/25 text-emerald-800 dark:text-emerald-200',
};

export function StatusPill({ status }: { status: string }) {
  const cls = STATUS_STYLES[status] || 'bg-ink/10 text-ink/70';
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wide ${cls}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export function SkillChips({ skills, max = 6 }: { skills: string[]; max?: number }) {
  const shown = skills.slice(0, max);
  const rest = skills.length - shown.length;
  return (
    <div className="flex flex-wrap gap-2">
      {shown.map((s) => (
        <span key={s} className="chip">
          {s}
        </span>
      ))}
      {rest > 0 && <span className="chip">+{rest}</span>}
    </div>
  );
}

export function MatchBadge({ score }: { score: number }) {
  const tone = score >= 70 ? 'bg-emerald-600' : score >= 40 ? 'bg-amber-500' : 'bg-slate-500';
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wide text-white ${tone}`}>
      {score}% match
    </span>
  );
}

export function Stars({ rating }: { rating: number }) {
  return (
    <span className="font-mono text-xs text-ink/70">
      ★ {rating.toFixed(1)}
    </span>
  );
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center justify-center px-8 py-16 text-center">
      <div className="font-display text-xl font-bold tracking-tight">{title}</div>
      <p className="mt-2 max-w-sm text-sm text-ink/60">{body}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

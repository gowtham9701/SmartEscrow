'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { SiteHeader } from '@/components/site-header';
import { Avatar, StatusPill, MatchBadge, SkillChips, EmptyState } from '@/components/ui';
import { ProfileEditor } from './profile-editor';
import { WalletPanel } from './wallet-panel';
import { ResumeManager, ResumeInsights } from './resume-manager';
import { FirmRegisterModal } from '@/components/firm-register-modal';
import { api, formatUSD, timeAgo } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { Application, Engagement, Job, Payment, PlatformStats, ResumeAnalysis, User, Wallet } from '@/lib/types';

interface DashboardData {
  user: User;
  stats: PlatformStats;
  engagements: Engagement[];
  payments: Payment[];
  applications: Application[];
  recommended_jobs?: Job[];
  jobs?: Job[];
  wallet?: Wallet;
  resume_insights?: ResumeAnalysis;
}

export function DashboardClient() {
  const { user, setUser } = useAuth();
  const isClient = user?.role === 'client';
  const [data, setData] = useState<DashboardData | null>(null);
  const [tab, setTab] = useState('overview');
  const [busy, setBusy] = useState(false);
  const [firmOpen, setFirmOpen] = useState(false);

  const needsFirm = isClient && !user?.firm_verified;
  const needsResume = !isClient && !(user?.resume_text || user?.resume_url);

  const load = useCallback(async () => {
    const d = await api.dashboard();
    setData(d as DashboardData);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
      await load();
    } finally {
      setBusy(false);
    }
  };

  const tabs = isClient
    ? ['overview', 'jobs', 'applicants', 'engagements', 'wallet', 'payments', 'profile']
    : ['overview', 'applications', 'resume', 'engagements', 'wallet', 'payments', 'profile'];

  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />

      <section className="container-x pt-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Avatar name={user?.full_name || '?'} hue={user?.avatar_hue} size={56} />
            <div>
              <div className="mono-label text-accent">{isClient ? 'Client Workspace' : 'Contributor Workspace'}</div>
              <h1 className="font-display text-2xl font-bold tracking-tight">
                {user?.full_name}
              </h1>
            </div>
          </div>
          {isClient ? (
            <Link href="/jobs/new" className="btn-navy">+ Post a Job</Link>
          ) : (
            <Link href="/jobs" className="btn-navy">Browse Jobs</Link>
          )}
        </div>

        {/* Tabs */}
        <div className="mt-8 flex gap-1 overflow-x-auto border-b border-ink/10">
          {tabs.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`whitespace-nowrap border-b-2 px-4 py-3 font-mono text-xs uppercase tracking-wide transition ${
                tab === t ? 'border-navy text-navy' : 'border-transparent text-ink/50 hover:text-ink'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </section>

      <section className="container-x py-8">
        {!data ? (
          <div className="grid gap-4 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-2xl bg-ink/5" />
            ))}
          </div>
        ) : (
          <>
            {tab === 'overview' && (
              <Overview
                data={data}
                isClient={isClient}
                onNavigate={setTab}
                needsFirm={needsFirm}
                needsResume={needsResume}
                onRegisterFirm={() => setFirmOpen(true)}
              />
            )}
            {tab === 'applications' && <ApplicationsPanel apps={data.applications} />}
            {tab === 'jobs' && <JobsPanel jobs={data.jobs || []} />}
            {tab === 'applicants' && (
              <ApplicantsPanel apps={data.applications} busy={busy} onStatus={(id, s) => act(() => api.setApplicationStatus(id, s))} />
            )}
            {tab === 'engagements' && (
              <EngagementsPanel
                engagements={data.engagements}
                isClient={isClient}
                busy={busy}
                onLog={(id, h, n) => act(() => api.logHours(id, h, n))}
                onFundEscrow={(id, h) => act(() => api.fundEscrow(id, h))}
              />
            )}
            {tab === 'wallet' && <WalletPanel />}
            {tab === 'resume' && <ResumeManager />}
            {tab === 'payments' && (
              <PaymentsPanel
                payments={data.payments}
                isClient={isClient}
                busy={busy}
                onRelease={(id) => act(() => api.releasePayment(id))}
              />
            )}
            {tab === 'profile' && <ProfileEditor />}
          </>
        )}
      </section>

      <FirmRegisterModal
        open={firmOpen}
        onClose={() => setFirmOpen(false)}
        onVerified={(u) => { setUser(u); load(); }}
      />
    </div>
  );
}

/* ----------------------------- Overview ----------------------------- */
function Overview({
  data,
  isClient,
  onNavigate,
  needsFirm,
  needsResume,
  onRegisterFirm,
}: {
  data: DashboardData;
  isClient: boolean;
  onNavigate: (tab: string) => void;
  needsFirm?: boolean;
  needsResume?: boolean;
  onRegisterFirm?: () => void;
}) {
  const totalBilled = data.payments.reduce((s, p) => s + (p.status === 'completed' ? p.amount_usd : 0), 0);
  const inEscrow = data.payments.filter((p) => p.status === 'in_escrow').reduce((s, p) => s + p.amount_usd, 0);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const firstName = (data.user.full_name || '').split(' ')[0];

  const pendingApps = data.applications.filter((a) => ['submitted', 'shortlisted', 'interview', 'offer'].includes(a.status)).length;
  const activeEng = data.engagements.filter((e) => e.status === 'active').length;

  const actions = isClient
    ? [
        { tag: 'Hire', title: 'Post a new role', body: 'Describe a job and let AI summarize it for applicants.', href: '/jobs/new' },
        { tag: 'Review', title: `${pendingApps} applicant${pendingApps === 1 ? '' : 's'} to review`, body: 'Shortlist, interview, and hire top talent.', tab: 'applicants' },
        { tag: 'Fund', title: 'Top up your wallet', body: 'Add funds and block escrow for engagements.', tab: 'wallet' },
        { tag: 'Discover', title: 'Browse vetted talent', body: 'Find AI-matched engineers for your needs.', href: '/talent' },
      ]
    : [
        { tag: 'Work', title: 'Find your next role', body: 'Browse AI-ranked jobs that match your stack.', href: '/jobs' },
        { tag: 'Track', title: `${pendingApps} application${pendingApps === 1 ? '' : 's'} in progress`, body: 'See where your applications stand.', tab: 'applications' },
        { tag: 'Deliver', title: `${activeEng} active engagement${activeEng === 1 ? '' : 's'}`, body: 'Log hours and track your work.', tab: 'engagements' },
        { tag: 'Earn', title: 'Check your wallet', body: 'View earnings and withdraw your balance.', tab: 'wallet' },
      ];

  const kpis = isClient
    ? [
        { label: 'Open Jobs', value: `${(data.jobs || []).filter((j) => j.status === 'open').length}` },
        { label: 'Applicants', value: `${data.applications.length}` },
        { label: 'Active Engagements', value: `${data.engagements.filter((e) => e.status === 'active').length}` },
        { label: 'In Escrow', value: formatUSD(inEscrow) },
      ]
    : [
        { label: 'Applications', value: `${data.applications.length}` },
        { label: 'Active Engagements', value: `${data.engagements.filter((e) => e.status === 'active').length}` },
        { label: 'Total Earned', value: formatUSD(totalBilled) },
        { label: 'In Escrow', value: formatUSD(inEscrow) },
      ];

  return (
    <div>
      {/* Welcome banner */}
      <div className="overflow-hidden rounded-2xl bg-navy p-8 text-paper md:p-10">
        <div className="mono-label text-paper/60">{greeting} 👋</div>
        <h2 className="display mt-4 text-[clamp(1.8rem,4.5vw,3.2rem)]">
          Welcome back, {firstName}.
        </h2>
        <p className="mt-4 max-w-xl font-mono text-sm text-paper/70">
          {isClient
            ? 'Your talent workspace is ready. What would you like to get done today?'
            : 'Your work hub is ready. Here\u2019s what you can do right now.'}
        </p>
      </div>

      {/* Onboarding prompts */}
      {needsFirm && (
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-amber-300 bg-amber-50 p-6">
          <div>
            <div className="font-display text-lg font-bold tracking-tight text-amber-800">Verify your firm to start hiring</div>
            <p className="mt-1 text-sm text-amber-700">Employer rights (posting jobs, hiring, escrow) unlock once your business is verified.</p>
          </div>
          <button onClick={onRegisterFirm} className="btn-navy">Register Firm</button>
        </div>
      )}
      {needsResume && (
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-amber-300 bg-amber-50 p-6">
          <div>
            <div className="font-display text-lg font-bold tracking-tight text-amber-800">Add your resume to get hired</div>
            <p className="mt-1 text-sm text-amber-700">Employers can only find and hire you once your freelancer profile has a resume.</p>
          </div>
          <button onClick={() => onNavigate('resume')} className="btn-navy">Upload Resume</button>
        </div>
      )}

      {/* What-to-do action feed */}
      <div className="mt-8">
        <div className="mono-label text-accent">What would you like to do?</div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {actions.map((a) => {
            const inner = (
              <>
                <div className="mono-label text-accent">{a.tag}</div>
                <div className="mt-3 font-display text-lg font-bold leading-tight tracking-tight">{a.title}</div>
                <p className="mt-2 flex-1 text-sm text-ink/60">{a.body}</p>
                <span className="mt-4 inline-flex items-center gap-1 font-mono text-xs uppercase tracking-wide text-navy">
                  Go <span>→</span>
                </span>
              </>
            );
            return a.href ? (
              <Link key={a.title} href={a.href} className="card group flex flex-col p-5 transition hover:-translate-y-1 hover:shadow-lg">
                {inner}
              </Link>
            ) : (
              <button
                key={a.title}
                onClick={() => a.tab && onNavigate(a.tab)}
                className="card group flex flex-col p-5 text-left transition hover:-translate-y-1 hover:shadow-lg"
              >
                {inner}
              </button>
            );
          })}
        </div>
      </div>

      {/* KPIs */}
      <div className="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-ink/10 bg-ink/10 md:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className="bg-surface p-6">
            <div className="font-display text-3xl font-bold tracking-tight">{k.value}</div>
            <div className="mono-label mt-2">{k.label}</div>
          </div>
        ))}
      </div>

      {!isClient && data.recommended_jobs && data.recommended_jobs.length > 0 && (
        <div className="mt-10">
          <div className="mono-label text-accent">✦ AI-Recommended For You</div>
          <h2 className="display mt-3 text-2xl">Best matches</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {data.recommended_jobs.map((j) => (
              <Link key={j.id} href={`/jobs/${j.id}`} className="card flex items-center justify-between gap-4 p-5 transition hover:shadow-lg">
                <div className="min-w-0">
                  <div className="truncate font-display text-base font-bold tracking-tight">{j.title}</div>
                  <div className="truncate font-mono text-xs text-ink/50">{j.company_name} · ${j.hourly_rate_min}–${j.hourly_rate_max}/hr</div>
                </div>
                {typeof j.match_score === 'number' && <MatchBadge score={j.match_score} />}
              </Link>
            ))}
          </div>
        </div>
      )}

      {!isClient && data.resume_insights?.has_resume && (
        <div className="mt-10">
          <ResumeInsights analysis={data.resume_insights} />
        </div>
      )}

      {isClient && (data.jobs || []).length > 0 && (
        <div className="mt-10">
          <div className="mono-label text-accent">Your Postings</div>
          <h2 className="display mt-3 text-2xl">Active jobs</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {(data.jobs || []).slice(0, 4).map((j) => (
              <Link key={j.id} href={`/jobs/${j.id}`} className="card flex items-center justify-between gap-4 p-5 transition hover:shadow-lg">
                <div className="min-w-0">
                  <div className="truncate font-display text-base font-bold tracking-tight">{j.title}</div>
                  <div className="truncate font-mono text-xs text-ink/50">{j.applicant_count || 0} applicants · {timeAgo(j.created_at)}</div>
                </div>
                <StatusPill status={j.status} />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ----------------------- Contributor Applications ----------------------- */
function ApplicationsPanel({ apps }: { apps: Application[] }) {
  if (apps.length === 0) {
    return <EmptyState title="No applications yet" body="Browse open roles and apply with your preferred rate." action={<Link href="/jobs" className="btn-navy">Find Work</Link>} />;
  }
  return (
    <div className="space-y-4">
      {apps.map((a) => (
        <div key={a.id} className="card flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="min-w-0">
            <Link href={`/jobs/${a.job_id}`} className="font-display text-lg font-bold tracking-tight hover:text-navy">
              {a.job?.title || 'Role'}
            </Link>
            <div className="font-mono text-xs text-ink/50">
              {a.job?.company_name} · Applied {timeAgo(a.created_at)}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="font-display text-lg font-bold">${a.proposed_hourly_rate}/hr</div>
              <div className="mono-label">your bid</div>
            </div>
            <StatusPill status={a.status} />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ----------------------------- Client Jobs ----------------------------- */
function JobsPanel({ jobs }: { jobs: Job[] }) {
  if (jobs.length === 0) {
    return <EmptyState title="No jobs posted" body="Post your first role to start receiving applicants." action={<Link href="/jobs/new" className="btn-navy">Post a Job</Link>} />;
  }
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {jobs.map((j) => (
        <Link key={j.id} href={`/jobs/${j.id}`} className="card p-6 transition hover:shadow-lg">
          <div className="flex items-start justify-between gap-3">
            <div className="font-display text-lg font-bold tracking-tight">{j.title}</div>
            <StatusPill status={j.status} />
          </div>
          <p className="mt-2 line-clamp-2 text-sm text-ink/60">{j.ai?.summary}</p>
          <div className="mt-4 flex items-center justify-between border-t border-ink/10 pt-3">
            <span className="font-mono text-xs text-ink/50">{j.applicant_count || 0} applicants</span>
            <span className="font-display font-bold">${j.hourly_rate_min}–${j.hourly_rate_max}/hr</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

/* --------------------------- Client Applicants --------------------------- */
const NEXT_STATUS: Record<string, string[]> = {
  submitted: ['shortlisted', 'rejected'],
  shortlisted: ['interview', 'rejected'],
  interview: ['offer', 'rejected'],
  offer: ['hired', 'rejected'],
};

function ApplicantsPanel({ apps, busy, onStatus }: { apps: Application[]; busy: boolean; onStatus: (id: string, s: string) => void }) {
  if (apps.length === 0) {
    return <EmptyState title="No applicants yet" body="Once contributors apply to your jobs, they'll appear here." />;
  }
  return (
    <div className="space-y-4">
      {apps.map((a) => (
        <div key={a.id} className="card p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-center gap-4">
              <Avatar name={a.contributor?.full_name || '?'} hue={a.contributor?.avatar_hue} />
              <div>
                <Link href={`/talent/${a.contributor_id}`} className="font-display text-lg font-bold tracking-tight hover:text-navy">
                  {a.contributor?.full_name}
                </Link>
                <div className="font-mono text-xs text-ink/50">{a.contributor?.title}</div>
                <div className="mt-1 font-mono text-[11px] text-ink/40">applied to {a.job?.title}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="font-display text-lg font-bold">${a.proposed_hourly_rate}/hr</div>
                <div className="mono-label">proposed</div>
              </div>
              <StatusPill status={a.status} />
            </div>
          </div>
          {a.cover_letter && <p className="mt-4 rounded-xl bg-ink/5 p-3 text-sm text-ink/70">{a.cover_letter}</p>}
          <div className="mt-4 flex flex-wrap gap-2">
            {(NEXT_STATUS[a.status] || []).map((s) => (
              <button
                key={s}
                disabled={busy}
                onClick={() => onStatus(a.id, s)}
                className={`rounded-full px-4 py-2 font-mono text-[11px] uppercase tracking-wide transition disabled:opacity-50 ${
                  s === 'rejected' ? 'border border-rose-300 text-rose-600 hover:bg-rose-50' : 'bg-navy text-paper hover:bg-navy-700'
                }`}
              >
                {s === 'hired' ? 'Hire' : s}
              </button>
            ))}
            {a.status === 'hired' && <span className="font-mono text-xs text-emerald-700">✓ Engagement created</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ----------------------------- Engagements ----------------------------- */
function EngagementsPanel({
  engagements,
  isClient,
  busy,
  onLog,
  onFundEscrow,
}: {
  engagements: Engagement[];
  isClient: boolean;
  busy: boolean;
  onLog: (id: string, hours: number, note: string) => void;
  onFundEscrow: (id: string, hours: number) => void;
}) {
  const [logId, setLogId] = useState<string | null>(null);
  const [hours, setHours] = useState(8);
  const [note, setNote] = useState('');
  const [fundId, setFundId] = useState<string | null>(null);
  const [fundHours, setFundHours] = useState(10);

  if (engagements.length === 0) {
    return <EmptyState title="No engagements yet" body={isClient ? 'Hire an applicant to start an engagement.' : 'Get hired to start logging hours.'} />;
  }

  return (
    <div className="space-y-4">
      {engagements.map((e) => (
        <div key={e.id} className="card p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="font-display text-lg font-bold tracking-tight">{e.title}</div>
              <div className="font-mono text-xs text-ink/50">
                {isClient ? e.contributor?.full_name : e.client?.company_name} · started {timeAgo(e.started_at)}
              </div>
            </div>
            <StatusPill status={e.status} />
          </div>

          <div className="mt-5 grid grid-cols-2 gap-4 md:grid-cols-4">
            <Metric label="Rate" value={`$${e.hourly_rate}/hr`} />
            <Metric label="Hours Logged" value={`${e.hours_logged}h`} />
            <Metric label="Total Billed" value={formatUSD(e.total_billed || e.hours_logged * e.hourly_rate)} />
            <Metric label="In Escrow" value={formatUSD(e.escrow_held || 0)} />
          </div>

          {e.timesheets.length > 0 && (
            <div className="mt-5">
              <div className="mono-label">Timesheets</div>
              <div className="mt-2 space-y-1">
                {e.timesheets.map((ts, i) => (
                  <div key={i} className="flex items-center justify-between border-b border-ink/5 py-1.5 text-sm">
                    <span className="text-ink/60">{ts.week} · {ts.note}</span>
                    <span className="font-display font-bold">{ts.hours}h</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Client: fund escrow (block funds) */}
          {isClient && e.status === 'active' && (
            <div className="mt-5">
              {fundId === e.id ? (
                <div className="flex flex-wrap items-end gap-3 rounded-xl bg-amber-50 p-4">
                  <label className="block">
                    <span className="mono-label mb-1 block">Hours to block</span>
                    <input type="number" min={1} value={fundHours} onChange={(ev) => setFundHours(Number(ev.target.value))} className="input w-28" />
                  </label>
                  <div className="font-mono text-xs text-ink/60">
                    = {formatUSD(fundHours * e.hourly_rate)} blocked in escrow
                  </div>
                  <button
                    disabled={busy}
                    onClick={() => {
                      onFundEscrow(e.id, fundHours);
                      setFundId(null);
                    }}
                    className="btn-navy disabled:opacity-50"
                  >
                    Block Funds
                  </button>
                  <button onClick={() => setFundId(null)} className="btn-ghost">Cancel</button>
                </div>
              ) : (
                <button onClick={() => setFundId(e.id)} className="btn-outline">🔒 Fund Escrow</button>
              )}
            </div>
          )}

          {/* Contributor: log hours */}
          {!isClient && e.status === 'active' && (
            <div className="mt-5">
              {logId === e.id ? (
                <div className="flex flex-wrap items-end gap-3 rounded-xl bg-ink/5 p-4">
                  <label className="block">
                    <span className="mono-label mb-1 block">Hours</span>
                    <input type="number" min={1} value={hours} onChange={(ev) => setHours(Number(ev.target.value))} className="input w-24" />
                  </label>
                  <label className="block flex-1">
                    <span className="mono-label mb-1 block">Note</span>
                    <input value={note} onChange={(ev) => setNote(ev.target.value)} placeholder="What did you work on?" className="input" />
                  </label>
                  <button
                    disabled={busy}
                    onClick={() => {
                      onLog(e.id, hours, note);
                      setLogId(null);
                      setNote('');
                    }}
                    className="btn-navy disabled:opacity-50"
                  >
                    Submit
                  </button>
                  <button onClick={() => setLogId(null)} className="btn-ghost">Cancel</button>
                </div>
              ) : (
                <button onClick={() => setLogId(e.id)} className="btn-outline">+ Log Hours</button>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ------------------------------ Payments ------------------------------ */
function PaymentsPanel({
  payments,
  isClient,
  busy,
  onRelease,
}: {
  payments: Payment[];
  isClient: boolean;
  busy: boolean;
  onRelease: (id: string) => void;
}) {
  if (payments.length === 0) {
    return <EmptyState title="No payments yet" body="Escrow records appear here once engagements are funded." />;
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-ink/10">
      <table className="w-full text-left text-sm">
        <thead className="bg-coal text-paper">
          <tr className="font-mono text-[11px] uppercase tracking-wide">
            <th className="px-5 py-3">Engagement</th>
            <th className="px-5 py-3">{isClient ? 'Contributor' : 'Client'}</th>
            <th className="px-5 py-3">Hours</th>
            <th className="px-5 py-3">Amount</th>
            <th className="px-5 py-3">Status</th>
            <th className="px-5 py-3">Date</th>
            {isClient && <th className="px-5 py-3"></th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-ink/10 bg-surface">
          {payments.map((p) => (
            <tr key={p.id}>
              <td className="px-5 py-4 font-medium">{p.engagement_title}</td>
              <td className="px-5 py-4 text-ink/60">{isClient ? p.contributor_name : p.client_name}</td>
              <td className="px-5 py-4">{p.hours}h</td>
              <td className="px-5 py-4 font-display font-bold">{formatUSD(p.amount_usd)}</td>
              <td className="px-5 py-4"><StatusPill status={p.status} /></td>
              <td className="px-5 py-4 font-mono text-xs text-ink/50">{timeAgo(p.created_at)}</td>
              {isClient && (
                <td className="px-5 py-4">
                  {p.status === 'in_escrow' && (
                    <button disabled={busy} onClick={() => onRelease(p.id)} className="rounded-full bg-emerald-600 px-3 py-1.5 font-mono text-[11px] uppercase tracking-wide text-white hover:bg-emerald-700 disabled:opacity-50">
                      Release
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-ink/5 p-4">
      <div className="font-display text-xl font-bold">{value}</div>
      <div className="mono-label mt-1">{label}</div>
    </div>
  );
}

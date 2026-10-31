'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { Verification } from '@/lib/types';

const DIMENSION_LABELS: Record<string, string> = {
  code_quality: 'Code Quality',
  languages: 'Language Breadth',
  impact: 'Impact (Stars)',
  velocity: 'Delivery Velocity',
  originality: 'Originality',
  discipline: 'Tests & Docs',
};

function tierColor(tier?: string) {
  switch (tier) {
    case 'A+':
    case 'A':
      return 'text-emerald-600 dark:text-emerald-400';
    case 'B':
      return 'text-sky-600 dark:text-sky-400';
    case 'C':
      return 'text-amber-600 dark:text-amber-400';
    default:
      return 'text-rose-600 dark:text-rose-400';
  }
}

export function VerificationPanel() {
  const { user, setUser } = useAuth();
  const [username, setUsername] = useState(user?.github_username || '');
  const [state, setState] = useState<Verification | null>(null);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    try {
      const v = await api.verification();
      setState(v);
      return v;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll while a verification is running.
  useEffect(() => {
    if (state?.status !== 'verifying') return;
    const id = setInterval(async () => {
      const v = await refresh();
      if (v && v.status !== 'verifying') {
        clearInterval(id);
        try {
          setUser(await api.me());
        } catch {
          /* ignore */
        }
      }
    }, 4000);
    return () => clearInterval(id);
  }, [state?.status, refresh, setUser]);

  const start = async () => {
    setError('');
    if (!username.trim()) {
      setError('Enter your GitHub username.');
      return;
    }
    try {
      await api.verifyGithub(username.trim());
      setState({ status: 'verifying', username: username.trim() });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not start verification.');
    }
  };

  const done = state?.status === 'done';
  const verifying = state?.status === 'verifying';

  return (
    <div className="max-w-3xl">
      <div className="mono-label text-accent">AI Technical Verification</div>
      <h2 className="display mt-3 text-2xl">Prove your skill with code, not keywords</h2>
      <p className="mt-2 text-sm text-ink/70">
        We analyze your public GitHub repositories — languages, real code quality
        (cyclomatic complexity &amp; maintainability), delivery velocity, impact, and
        testing discipline — to produce an objective talent grade.
      </p>

      <div className="mt-6 card p-5">
        <label className="mono-label text-ink/60">GitHub Username</label>
        <div className="mt-2 flex flex-wrap gap-2">
          <input
            className="input flex-1"
            placeholder="e.g. octocat"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={verifying}
          />
          <button className="btn-navy" onClick={start} disabled={verifying}>
            {verifying ? 'Verifying…' : done ? 'Re-verify' : 'Verify my GitHub'}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-rose-600 dark:text-rose-400">{error}</p>}
        {verifying && (
          <p className="mt-3 font-mono text-xs text-ink/60">
            ⏳ Analyzing <strong>{state?.username}</strong>&apos;s repositories… this can take up to a minute.
          </p>
        )}
        {state?.status === 'failed' && (
          <p className="mt-3 text-sm text-rose-600 dark:text-rose-400">
            {state.error || 'Verification failed.'}
          </p>
        )}
      </div>

      {done && state && (
        <div className="mt-6 card p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="mono-label text-ink/60">Talent Grade</div>
              <div className="flex items-end gap-3">
                <span className="font-display text-5xl font-bold tracking-tight">{state.talent_grade}</span>
                <span className={`font-display text-3xl font-bold ${tierColor(state.tier)}`}>{state.tier}</span>
              </div>
            </div>
            <div className="text-right font-mono text-xs text-ink/60">
              <div>{state.public_repos} public repos · {state.followers} followers</div>
              <div>{state.total_stars?.toLocaleString()} total stars</div>
              <div>{state.repos_active_last_year} repos active last year</div>
              {state.profile_url && (
                <a href={state.profile_url} target="_blank" rel="noreferrer" className="text-navy hover:underline dark:text-sky-300">
                  View GitHub profile ↗
                </a>
              )}
            </div>
          </div>

          <div className="mt-6 space-y-3">
            {Object.entries(state.breakdown || {}).map(([k, v]) => (
              <div key={k}>
                <div className="flex justify-between font-mono text-xs text-ink/70">
                  <span>{DIMENSION_LABELS[k] || k}</span>
                  <span>{Math.round(v)}/100</span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-ink/10">
                  <div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(100, v)}%` }} />
                </div>
              </div>
            ))}
          </div>

          {!state.code_quality_measured && (
            <p className="mt-4 font-mono text-[11px] text-ink/50">
              Note: code-quality was estimated (no analyzable Python source found in top repos).
            </p>
          )}

          {state.verified_skills && state.verified_skills.length > 0 && (
            <div className="mt-6">
              <div className="mono-label text-ink/60">Verified Skills (from real code)</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {state.verified_skills.map((s) => (
                  <span key={s} className="chip border-emerald-400/50 text-emerald-700 dark:text-emerald-300">
                    ✓ {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

'use client';

import { useCallback, useEffect, useState } from 'react';
import { api, formatUSD } from '@/lib/api';
import type { Dispute, Engagement } from '@/lib/types';

const VERDICT_LABELS: Record<string, string> = {
  release: 'Release to contributor',
  refund: 'Refund to client',
  split: 'Split 50 / 50',
};

function StatusBadge({ d }: { d: Dispute }) {
  if (d.status === 'resolved') {
    return (
      <span className="chip border-emerald-400/50 text-emerald-700 dark:text-emerald-300">
        Resolved · {d.verdict}
      </span>
    );
  }
  return (
    <span className="chip border-amber-400/50 text-amber-700 dark:text-amber-300">
      Voting · {d.votes_cast}/{d.jury_size}
    </span>
  );
}

export function DisputesPanel({ engagements }: { engagements: Engagement[] }) {
  const [mine, setMine] = useState<Dispute[]>([]);
  const [jury, setJury] = useState<Dispute[]>([]);
  const [engId, setEngId] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const d = await api.myDisputes();
      setMine(d.my_disputes);
      setJury(d.jury_duty);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Engagements that have funds in escrow are eligible for a dispute.
  const disputable = engagements.filter((e) => (e.escrow_held || 0) > 0);

  const raise = async () => {
    setError('');
    if (!engId) {
      setError('Select an engagement with escrowed funds.');
      return;
    }
    if (reason.trim().length < 3) {
      setError('Please describe the issue.');
      return;
    }
    setBusy(true);
    try {
      await api.raiseDispute(engId, reason.trim());
      setReason('');
      setEngId('');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not raise dispute.');
    } finally {
      setBusy(false);
    }
  };

  const vote = async (id: string, verdict: 'release' | 'refund' | 'split') => {
    setBusy(true);
    try {
      await api.voteDispute(id, verdict);
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-10">
      {/* Raise a dispute */}
      <div className="max-w-2xl">
        <div className="mono-label text-accent">Peer-Led Dispute Resolution</div>
        <h2 className="display mt-3 text-2xl">Raise a milestone dispute</h2>
        <p className="mt-2 text-sm text-ink/70">
          If a milestone is contested, a blind, randomized jury of three senior
          engineers reviews it. Their majority verdict automatically releases,
          refunds, or splits the escrowed funds.
        </p>
        <div className="mt-5 card p-5">
          <label className="mono-label text-ink/60">Engagement in escrow</label>
          <select className="input mt-2" value={engId} onChange={(e) => setEngId(e.target.value)}>
            <option value="">Select an engagement…</option>
            {disputable.map((e) => (
              <option key={e.id} value={e.id}>
                {e.title} — {formatUSD(e.escrow_held || 0)} in escrow
              </option>
            ))}
          </select>
          {disputable.length === 0 && (
            <p className="mt-2 font-mono text-xs text-ink/50">
              You have no engagements with escrowed funds to dispute.
            </p>
          )}
          <textarea
            className="input mt-3 min-h-[90px]"
            placeholder="Describe the issue with the delivered work…"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          {error && <p className="mt-2 text-sm text-rose-600 dark:text-rose-400">{error}</p>}
          <button className="btn-navy mt-3" onClick={raise} disabled={busy}>
            Raise dispute
          </button>
        </div>
      </div>

      {/* Jury duty */}
      {jury.length > 0 && (
        <div>
          <div className="mono-label text-accent">⚖ Jury Duty</div>
          <h2 className="display mt-3 text-2xl">Cases awaiting your verdict</h2>
          <p className="mt-2 text-sm text-ink/70">
            You were randomly selected to arbitrate these cases. Parties are
            anonymized to keep your judgment impartial.
          </p>
          <div className="mt-5 grid gap-4">
            {jury.map((d) => (
              <div key={d.id} className="card p-5">
                <div className="flex items-center justify-between">
                  <div className="font-display text-base font-bold">{d.engagement_title || 'Engagement'}</div>
                  <StatusBadge d={d} />
                </div>
                <div className="mt-1 font-mono text-xs text-ink/50">
                  {formatUSD(d.amount_usd || 0)} in escrow · {d.raised_by} vs {d.against}
                </div>
                <p className="mt-3 rounded-xl bg-ink/5 p-3 text-sm text-ink/80">“{d.reason}”</p>
                {d.status === 'voting' && !d.has_voted ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {(['release', 'refund', 'split'] as const).map((v) => (
                      <button key={v} className="btn-outline" onClick={() => vote(d.id, v)} disabled={busy}>
                        {VERDICT_LABELS[v]}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 font-mono text-xs text-emerald-600 dark:text-emerald-400">
                    {d.has_voted ? '✓ You have voted on this case.' : `Resolved: ${d.verdict}`}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* My disputes */}
      <div>
        <div className="mono-label text-accent">Your Disputes</div>
        <h2 className="display mt-3 text-2xl">Cases you are party to</h2>
        {mine.length === 0 ? (
          <p className="mt-3 text-sm text-ink/60">You have not raised or received any disputes.</p>
        ) : (
          <div className="mt-5 grid gap-4">
            {mine.map((d) => (
              <div key={d.id} className="card p-5">
                <div className="flex items-center justify-between">
                  <div className="font-display text-base font-bold">{d.engagement_title || 'Engagement'}</div>
                  <StatusBadge d={d} />
                </div>
                <div className="mt-1 font-mono text-xs text-ink/50">
                  {formatUSD(d.amount_usd || 0)} in escrow
                </div>
                <p className="mt-3 rounded-xl bg-ink/5 p-3 text-sm text-ink/80">“{d.reason}”</p>
                {d.status === 'resolved' && d.tally && (
                  <p className="mt-3 font-mono text-xs text-ink/60">
                    Jury verdict: <strong>{d.verdict}</strong> (release {d.tally.release || 0} · refund{' '}
                    {d.tally.refund || 0} · split {d.tally.split || 0})
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

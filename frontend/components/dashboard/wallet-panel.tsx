'use client';

import { useCallback, useEffect, useState } from 'react';
import { PaymentGatewayModal } from '@/components/payment-gateway-modal';
import { EmptyState } from '@/components/ui';
import { api, formatUSD, timeAgo } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { WalletSummary } from '@/lib/types';

const TX_LABELS: Record<string, string> = {
  deposit: 'Wallet top-up',
  withdrawal: 'Payout to bank',
  escrow_block: 'Escrow blocked',
  escrow_release: 'Escrow released',
  earning: 'Earning received',
};

export function WalletPanel() {
  const { user } = useAuth();
  const isClient = user?.role === 'client';
  const [data, setData] = useState<WalletSummary | null>(null);
  const [gatewayOpen, setGatewayOpen] = useState(false);
  const [withdrawAmount, setWithdrawAmount] = useState(500);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    const d = await api.wallet();
    setData(d);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const withdraw = async () => {
    setBusy(true);
    setMsg('');
    try {
      await api.withdraw(withdrawAmount);
      setMsg('Payout initiated.');
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Withdrawal failed');
    } finally {
      setBusy(false);
    }
  };

  if (!data) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        {[...Array(2)].map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-2xl bg-ink/5" />
        ))}
      </div>
    );
  }

  const { wallet, transactions, payment_methods } = data;

  return (
    <div>
      {/* Balance cards */}
      <div className="grid gap-6 md:grid-cols-[1.4fr_1fr]">
        <div className="rounded-2xl bg-gradient-to-br from-navy to-ink p-8 text-paper">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-paper/60">
            Available Balance
          </div>
          <div className="mt-3 font-display text-5xl font-bold tracking-tight">
            {formatUSD(wallet.available_balance)}
          </div>
          <div className="mt-6 flex items-center gap-6">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-paper/50">
                {isClient ? 'Blocked in Escrow' : 'Pending'}
              </div>
              <div className="mt-1 font-display text-xl font-bold text-amber-300">
                {formatUSD(wallet.blocked_balance)}
              </div>
            </div>
            <div className="h-10 w-px bg-paper/20" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-paper/50">Currency</div>
              <div className="mt-1 font-display text-xl font-bold">{wallet.currency}</div>
            </div>
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            {isClient ? (
              <button onClick={() => setGatewayOpen(true)} className="btn-ink bg-paper text-coal hover:bg-paper/90">
                + Add Funds
              </button>
            ) : (
              <div className="flex items-end gap-2">
                <label className="block">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-paper/50">Withdraw</span>
                  <input
                    type="number"
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(Number(e.target.value))}
                    className="mt-1 w-28 rounded-lg bg-paper/10 px-3 py-2 text-sm text-paper outline-none"
                  />
                </label>
                <button onClick={withdraw} disabled={busy} className="btn-ink bg-paper text-coal hover:bg-paper/90 disabled:opacity-50">
                  Payout
                </button>
              </div>
            )}
          </div>
          {msg && <div className="mt-3 font-mono text-[11px] text-paper/70">{msg}</div>}
        </div>

        {/* QuickRide-style explainer / escrow security */}
        <div className="card p-6">
          <div className="mono-label text-accent">🔒 Secured Escrow</div>
          <p className="mt-3 text-sm text-ink/70">
            {isClient
              ? 'When you fund an engagement, the amount is blocked in escrow — guaranteeing the contributor gets paid while protecting your funds until you release on verified delivery.'
              : 'When a client funds your engagement, the amount is blocked in their wallet and guaranteed to you. On release, it lands in your available balance instantly.'}
          </p>
          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-ink/5 p-3">
              <div className="font-display text-lg font-bold">{formatUSD(wallet.available_balance)}</div>
              <div className="mono-label mt-1">Spendable</div>
            </div>
            <div className="rounded-xl bg-amber-50 dark:bg-amber-500/15 p-3">
              <div className="font-display text-lg font-bold text-amber-700 dark:text-amber-200">{formatUSD(wallet.blocked_balance)}</div>
              <div className="mono-label mt-1">Blocked</div>
            </div>
          </div>
        </div>
      </div>

      {/* Saved cards */}
      {isClient && (
        <div className="mt-10">
          <div className="flex items-center justify-between">
            <div className="mono-label text-accent">Payment Methods</div>
            <button onClick={() => setGatewayOpen(true)} className="font-mono text-xs uppercase tracking-wide text-navy hover:underline">
              + Add card
            </button>
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {payment_methods.length === 0 ? (
              <div className="card p-5 text-sm text-ink/50">No saved cards yet.</div>
            ) : (
              payment_methods.map((pm) => (
                <div key={pm.id} className="rounded-2xl bg-gradient-to-br from-ink to-navy-700 p-5 text-paper">
                  <div className="flex items-center justify-between">
                    <span className="font-display text-sm font-bold uppercase">{pm.brand}</span>
                    {pm.is_default === 1 && <span className="font-mono text-[9px] uppercase text-paper/60">Default</span>}
                  </div>
                  <div className="mt-6 font-mono tracking-widest">•••• {pm.last4}</div>
                  <div className="mt-3 flex justify-between font-mono text-[10px] text-paper/60">
                    <span>{pm.holder_name}</span>
                    <span>{String(pm.exp_month).padStart(2, '0')}/{String(pm.exp_year).slice(-2)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Transactions */}
      <div className="mt-10">
        <div className="mono-label text-accent">Transaction History</div>
        {transactions.length === 0 ? (
          <div className="mt-4">
            <EmptyState title="No transactions yet" body="Your wallet activity will appear here." />
          </div>
        ) : (
          <div className="mt-4 overflow-hidden rounded-2xl border border-ink/10">
            <table className="w-full text-left text-sm">
              <thead className="bg-coal text-paper">
                <tr className="font-mono text-[11px] uppercase tracking-wide">
                  <th className="px-5 py-3">Type</th>
                  <th className="px-5 py-3">Note</th>
                  <th className="px-5 py-3">Amount</th>
                  <th className="px-5 py-3">Balance</th>
                  <th className="px-5 py-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink/10 bg-surface">
                {transactions.map((t) => (
                  <tr key={t.id}>
                    <td className="px-5 py-4 font-medium">{TX_LABELS[t.type] || t.type}</td>
                    <td className="px-5 py-4 text-ink/60">{t.note}</td>
                    <td className={`px-5 py-4 font-display font-bold ${t.amount >= 0 ? 'text-emerald-600 dark:text-emerald-300' : 'text-ink'}`}>
                      {t.amount >= 0 ? '+' : ''}{formatUSD(t.amount)}
                    </td>
                    <td className="px-5 py-4 font-mono text-xs text-ink/50">{formatUSD(t.available_after)}</td>
                    <td className="px-5 py-4 font-mono text-xs text-ink/50">{timeAgo(t.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <PaymentGatewayModal
        open={gatewayOpen}
        onClose={() => setGatewayOpen(false)}
        onSuccess={() => load()}
        holderName={user?.full_name}
      />
    </div>
  );
}

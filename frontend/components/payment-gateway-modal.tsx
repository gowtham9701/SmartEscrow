'use client';

import { useState } from 'react';
import { api, formatUSD } from '@/lib/api';
import type { Wallet } from '@/lib/types';

type Step = 'amount' | 'card' | 'pin' | 'processing' | 'success' | 'error';

function formatCard(value: string) {
  const digits = value.replace(/\D/g, '').slice(0, 16);
  return digits.replace(/(.{4})/g, '$1 ').trim();
}

export function PaymentGatewayModal({
  open,
  onClose,
  onSuccess,
  presetAmount,
  holderName,
}: {
  open: boolean;
  onClose: () => void;
  onSuccess: (wallet: Wallet) => void;
  presetAmount?: number;
  holderName?: string;
}) {
  const [step, setStep] = useState<Step>('amount');
  const [amount, setAmount] = useState(presetAmount || 1000);
  const [cardNumber, setCardNumber] = useState('');
  const [holder, setHolder] = useState((holderName || '').toUpperCase());
  const [expMonth, setExpMonth] = useState('');
  const [expYear, setExpYear] = useState('');
  const [cvv, setCvv] = useState('');
  const [pin, setPin] = useState('');
  const [showPin, setShowPin] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ brand: string; last4: string; ref: string } | null>(null);

  if (!open) return null;

  const reset = () => {
    setStep('amount');
    setCardNumber('');
    setHolder((holderName || '').toUpperCase());
    setExpMonth('');
    setExpYear('');
    setCvv('');
    setPin('');
    setError('');
    setResult(null);
  };

  const close = () => {
    reset();
    onClose();
  };

  const submitPayment = async () => {
    setStep('processing');
    setError('');
    // Simulated gateway latency for realism.
    await new Promise((r) => setTimeout(r, 1800));
    try {
      const res = await api.deposit({
        amount,
        card_number: cardNumber.replace(/\s/g, ''),
        exp_month: Number(expMonth),
        exp_year: Number(expYear.length === 2 ? `20${expYear}` : expYear),
        cvv,
        pin,
        holder_name: holder,
        save_card: true,
      });
      setResult({ brand: res.brand, last4: res.last4, ref: res.gateway_ref });
      setStep('success');
      onSuccess(res.wallet);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment failed');
      setStep('error');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md overflow-hidden rounded-2xl bg-surface shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between bg-navy px-6 py-4 text-paper">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em]">🔒 SmartEscrow Pay</span>
          </div>
          <button onClick={close} className="font-mono text-lg leading-none text-paper/70 hover:text-paper">
            ×
          </button>
        </div>

        <div className="p-6">
          {step === 'amount' && (
            <div>
              <div className="mono-label">Add funds to wallet</div>
              <h3 className="mt-2 font-display text-2xl font-bold tracking-tight">Top Up</h3>
              <label className="mt-6 block">
                <span className="mono-label mb-2 block">Amount (USD)</span>
                <input
                  type="number"
                  min={10}
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                  className="input text-2xl font-display font-bold"
                />
              </label>
              <div className="mt-4 flex flex-wrap gap-2">
                {[500, 1000, 5000, 10000].map((a) => (
                  <button
                    key={a}
                    onClick={() => setAmount(a)}
                    className={`rounded-full px-4 py-2 font-mono text-xs transition ${
                      amount === a ? 'bg-navy text-paper' : 'border border-ink/15 text-ink/60 hover:border-ink'
                    }`}
                  >
                    {formatUSD(a)}
                  </button>
                ))}
              </div>
              <button onClick={() => setStep('card')} className="btn-navy mt-6 w-full">
                Continue
              </button>
            </div>
          )}

          {step === 'card' && (
            <div>
              <div className="mono-label">Card details</div>
              <h3 className="mt-2 font-display text-2xl font-bold tracking-tight">
                Pay {formatUSD(amount)}
              </h3>

              {/* Card visual */}
              <div className="mt-5 rounded-2xl bg-gradient-to-br from-navy to-ink p-5 text-paper">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase tracking-widest text-paper/60">SmartEscrow</span>
                  <span className="font-mono text-[10px] text-paper/60">VIRTUAL</span>
                </div>
                <div className="mt-6 font-mono text-lg tracking-widest">
                  {cardNumber || '•••• •••• •••• ••••'}
                </div>
                <div className="mt-4 flex items-center justify-between font-mono text-[11px] text-paper/70">
                  <span>{holder || 'CARDHOLDER NAME'}</span>
                  <span>{expMonth || 'MM'}/{expYear || 'YY'}</span>
                </div>
              </div>

              <div className="mt-5 space-y-3">
                <input
                  value={cardNumber}
                  onChange={(e) => setCardNumber(formatCard(e.target.value))}
                  placeholder="Card number"
                  inputMode="numeric"
                  className="input"
                />
                <input
                  value={holder}
                  onChange={(e) => setHolder(e.target.value.toUpperCase())}
                  placeholder="Cardholder name"
                  className="input"
                />
                <div className="grid grid-cols-3 gap-3">
                  <input value={expMonth} onChange={(e) => setExpMonth(e.target.value.replace(/\D/g, '').slice(0, 2))} placeholder="MM" inputMode="numeric" className="input" />
                  <input value={expYear} onChange={(e) => setExpYear(e.target.value.replace(/\D/g, '').slice(0, 4))} placeholder="YY" inputMode="numeric" className="input" />
                  <input value={cvv} onChange={(e) => setCvv(e.target.value.replace(/\D/g, '').slice(0, 4))} placeholder="CVV" inputMode="numeric" className="input" />
                </div>
              </div>

              <div className="mt-5 flex gap-3">
                <button onClick={() => setStep('amount')} className="btn-ghost flex-1">Back</button>
                <button
                  onClick={() => setStep('pin')}
                  disabled={cardNumber.replace(/\s/g, '').length < 12 || !cvv || !expMonth || !expYear}
                  className="btn-navy flex-[2] disabled:opacity-50"
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {step === 'pin' && (
            <div className="text-center">
              <div className="mono-label">Authorize payment</div>
              <h3 className="mt-2 font-display text-2xl font-bold tracking-tight">Enter PIN</h3>
              <p className="mt-2 text-sm text-ink/60">
                Confirm {formatUSD(amount)} payment with your 4-digit card PIN.
              </p>
              <div className="relative mx-auto mt-6 w-52">
                <input
                  value={pin}
                  onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 4))}
                  inputMode="numeric"
                  maxLength={4}
                  type={showPin ? 'text' : 'password'}
                  placeholder="••••"
                  className="input w-full pr-12 text-center text-3xl tracking-[0.5em]"
                />
                <button
                  type="button"
                  onClick={() => setShowPin((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/40 hover:text-ink"
                  aria-label={showPin ? 'Hide PIN' : 'Show PIN'}
                >
                  {showPin ? '🙈' : '👁'}
                </button>
              </div>
              <div className="mt-6 flex gap-3">
                <button onClick={() => setStep('card')} className="btn-ghost flex-1">Back</button>
                <button onClick={submitPayment} disabled={pin.length < 4} className="btn-navy flex-[2] disabled:opacity-50">
                  Pay {formatUSD(amount)}
                </button>
              </div>
            </div>
          )}

          {step === 'processing' && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="h-14 w-14 animate-spin rounded-full border-4 border-ink/10 border-t-navy" />
              <div className="mt-6 font-display text-lg font-bold tracking-tight">Processing…</div>
              <p className="mt-2 font-mono text-xs text-ink/50">Securely contacting your bank</p>
            </div>
          )}

          {step === 'success' && result && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-500/25 text-3xl text-emerald-600 dark:text-emerald-300">
                ✓
              </div>
              <div className="mt-5 font-display text-2xl font-bold tracking-tight">Payment Successful</div>
              <p className="mt-2 text-sm text-ink/60">
                {formatUSD(amount)} added via {result.brand} •••• {result.last4}
              </p>
              <p className="mt-1 font-mono text-[10px] text-ink/40">Ref: {result.ref}</p>
              <button onClick={close} className="btn-navy mt-6 w-full">Done</button>
            </div>
          )}

          {step === 'error' && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-rose-100 dark:bg-rose-500/25 text-3xl text-rose-600 dark:text-rose-300">
                ×
              </div>
              <div className="mt-5 font-display text-2xl font-bold tracking-tight">Payment Failed</div>
              <p className="mt-2 text-sm text-rose-600 dark:text-rose-300">{error}</p>
              <div className="mt-6 flex w-full gap-3">
                <button onClick={close} className="btn-ghost flex-1">Cancel</button>
                <button onClick={() => setStep('card')} className="btn-navy flex-1">Try Again</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

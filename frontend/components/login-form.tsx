"use client";

import { useState } from 'react';

export function LoginForm() {
  const [email, setEmail] = useState('admin@smartescrow.io');
  const [password, setPassword] = useState('SmartEscrow123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      localStorage.setItem('smartescrow_token', data.access_token);
      localStorage.setItem('smartescrow_user', JSON.stringify(data.user));
      setSuccess(true);
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_#0f172a,_#020617_60%)] px-4 text-slate-100">
      <div className="w-full max-w-6xl overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/70 shadow-2xl shadow-sky-900/20 backdrop-blur-xl">
        <div className="grid md:grid-cols-2">
          <div className="bg-gradient-to-br from-sky-500/20 via-slate-900 to-slate-950 p-10">
            <div className="text-xs uppercase tracking-[0.3em] text-sky-300">SmartEscrow</div>
            <h1 className="mt-8 text-4xl font-semibold">Trust at the speed of code.</h1>
            <p className="mt-6 max-w-md text-slate-300">
              Platform-grade escrow, AI verification, and peer dispute resolution for global software delivery.
            </p>
            <div className="mt-10 grid gap-4 text-sm text-slate-200">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">Fiat payout release after verified GitHub merge events.</div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">Local LLM code-quality grading with objective talent scoring.</div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">Blind peer jury dispute resolution across engineering experts.</div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="p-10 md:p-14">
            <div className="mb-8">
              <div className="text-sm uppercase tracking-[0.2em] text-slate-400">Access portal</div>
              <h2 className="mt-3 text-3xl font-semibold">Welcome back</h2>
            </div>

            <div className="space-y-5">
              <label className="block">
                <span className="mb-2 block text-sm text-slate-300">Email</span>
                <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 outline-none ring-0 transition focus:border-sky-400" placeholder="you@company.com" />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm text-slate-300">Password</span>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 outline-none ring-0 transition focus:border-sky-400" placeholder="••••••••" />
              </label>
            </div>

            {error && <div className="mt-5 rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">{error}</div>}
            {success && <div className="mt-5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">Signed in successfully.</div>}

            <button disabled={loading} type="submit" className="mt-8 w-full rounded-xl bg-sky-500 px-4 py-3 font-medium text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60">
              {loading ? 'Signing in...' : 'Sign in'}
            </button>

            <div className="mt-6 text-xs text-slate-400">
              Demo users: admin@smartescrow.io / SmartEscrow123!
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

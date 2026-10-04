'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { SiteHeader } from '@/components/site-header';
import { useAuth } from '@/lib/auth-context';

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(identifier, password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const demo = (who: 'contributor' | 'client') => {
    if (who === 'contributor') {
      setIdentifier('ava.chen@smartescrow.io');
      setPassword('Password123!');
    } else {
      setIdentifier('client@apexlabs.io');
      setPassword('Password123!');
    }
  };

  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />
      <section className="container-x grid gap-12 py-16 md:grid-cols-[1.2fr_1fr] md:items-center">
        <div className="hidden md:block">
          <div className="mono-label text-accent">Welcome back</div>
          <h1 className="display mt-6 text-[clamp(2.4rem,5.5vw,4.5rem)]">
            Sign in to
            <br />
            SmartEscrow.
          </h1>
          <p className="mt-8 max-w-md font-mono text-sm leading-relaxed text-ink/70">
            Access your dashboard to manage applications, engagements, payments, and your public
            profile.
          </p>
        </div>

        <div className="card mx-auto w-full max-w-md p-8 md:p-10">
          <div className="font-display text-2xl font-bold tracking-tight">Welcome to SmartEscrow</div>
          <form onSubmit={submit} className="mt-8 space-y-4">
            <label className="block">
              <span className="mono-label mb-2 block">Username or Email</span>
              <input
                className="input"
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="username or you@email.com"
                required
              />
            </label>
            <label className="block">
              <span className="mono-label mb-2 block">Password</span>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </label>

            {error && (
              <div className="rounded-xl border border-rose-300 dark:border-rose-500/40 bg-rose-50 dark:bg-rose-500/15 px-3 py-2 text-sm text-rose-700 dark:text-rose-200">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-navy w-full disabled:opacity-60">
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 flex items-center justify-between text-xs text-ink/60">
            <span>
              New here?{' '}
              <Link href="/register" className="font-semibold text-navy hover:underline">
                Create account
              </Link>
            </span>
          </div>

          <div className="mt-6 rounded-xl border border-ink/10 bg-surface p-4">
            <div className="mono-label">Demo accounts</div>
            <div className="mt-3 flex gap-2">
              <button onClick={() => demo('contributor')} className="btn-outline flex-1 py-2 text-xs">
                Contributor
              </button>
              <button onClick={() => demo('client')} className="btn-outline flex-1 py-2 text-xs">
                Client
              </button>
            </div>
            <p className="mt-2 font-mono text-[10px] text-ink/50">Password: Password123!</p>
          </div>
        </div>
      </section>
    </div>
  );
}

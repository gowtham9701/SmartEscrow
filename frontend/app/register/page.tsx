'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { SiteHeader } from '@/components/site-header';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';
import type { Role } from '@/lib/types';

interface StartResult {
  registration_id: string;
  email: string;
  phone: string;
  delivery: string;
  demo_email_otp?: string;
}

function RegisterForm() {
  const { completeRegistration } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const initialRole = (params.get('role') as Role) || 'contributor';

  const [step, setStep] = useState<'details' | 'otp'>('details');
  const [role, setRole] = useState<Role>(initialRole === 'client' ? 'client' : 'contributor');

  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [title, setTitle] = useState('');
  const [rate, setRate] = useState(55);
  const [company, setCompany] = useState('');
  const [skills, setSkills] = useState('');

  const [startRes, setStartRes] = useState<StartResult | null>(null);
  const [emailOtp, setEmailOtp] = useState('');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const startRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.registerStart({
        username,
        email,
        phone,
        password,
        full_name: fullName,
        role,
        title: role === 'contributor' ? title || 'Independent Contributor' : undefined,
        hourly_rate_usd: role === 'contributor' ? rate : undefined,
        company_name: role === 'client' ? company : undefined,
        skills: skills ? skills.split(',').map((s) => s.trim()).filter(Boolean) : [],
      });
      setStartRes(res);
      setStep('otp');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!startRes) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.registerVerify(startRes.registration_id, emailOtp);
      completeRegistration(res.access_token, res.user);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    if (!startRes) return;
    setError('');
    try {
      const res = await api.registerResend(startRes.registration_id);
      setStartRes({
        ...startRes,
        delivery: res.delivery,
        demo_email_otp: res.demo_email_otp,
      });
      setEmailOtp('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not resend');
    }
  };

  return (
    <section className="container-x grid gap-12 py-14 md:grid-cols-[1fr_1.1fr] md:items-start">
      <div className="hidden md:block md:pt-6">
        <div className="mono-label text-accent">{step === 'otp' ? 'Verify your identity' : 'Create account'}</div>
        <h1 className="display mt-6 text-[clamp(2.4rem,5.5vw,4.5rem)]">
          Join
          <br />
          SmartEscrow.
        </h1>
        <p className="mt-8 max-w-md font-mono text-sm leading-relaxed text-ink/70">
          {step === 'otp'
            ? 'We sent a 6-digit code to your email. Enter it to activate your account securely.'
            : "Whether you're hiring elite talent or offering your skills, you're minutes from a verified live profile."}
        </p>
        <ul className="mt-8 space-y-3 text-sm text-ink/70">
          <li>— Email OTP verification (free)</li>
          <li>— Sign in with your username and password</li>
          <li>— AI-summarized job posts and ranked matches</li>
        </ul>
      </div>

      <div className="card w-full p-8 md:p-10">
        {step === 'details' ? (
          <>
            <div className="grid grid-cols-2 gap-2 rounded-xl bg-ink/5 p-1">
              {(['contributor', 'client'] as Role[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRole(r)}
                  className={`rounded-lg px-4 py-2.5 font-mono text-xs uppercase tracking-wide transition ${
                    role === r ? 'bg-navy text-paper' : 'text-ink/60 hover:text-ink'
                  }`}
                >
                  {r === 'contributor' ? 'I want work' : 'I want to hire'}
                </button>
              ))}
            </div>

            <form onSubmit={startRegistration} className="mt-6 space-y-4">
              <Field label="Full Name" value={fullName} onChange={setFullName} required placeholder="e.g. Gowtham Kumar" />
              <Field label="Username" value={username} onChange={(v) => setUsername(v.toLowerCase())} required placeholder="e.g. gowtham" hint="Letters, numbers, dots and underscores" />
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Email" type="email" value={email} onChange={setEmail} required placeholder="you@email.com" />
                <Field label="Mobile Number" value={phone} onChange={setPhone} required placeholder="+91 90000 00000" />
              </div>
              <Field label="Password" type="password" value={password} onChange={setPassword} required hint="Min 6 characters" />

              {role === 'contributor' ? (
                <>
                  <Field label="Professional Title" value={title} onChange={setTitle} placeholder="e.g. Senior Full-Stack Engineer" />
                  <div className="grid gap-4 sm:grid-cols-2">
                    <label className="block">
                      <span className="mono-label mb-2 block">Hourly Rate (USD)</span>
                      <input type="number" min={10} className="input" value={rate} onChange={(e) => setRate(Number(e.target.value))} />
                    </label>
                    <Field label="Skills (comma-separated)" value={skills} onChange={setSkills} placeholder="Python, React" />
                  </div>
                </>
              ) : (
                <>
                  <Field label="Company Name" value={company} onChange={setCompany} placeholder="Acme Inc." />
                  <Field label="Focus Areas (comma-separated)" value={skills} onChange={setSkills} placeholder="Backend, AI, Security" />
                </>
              )}

              {error && <div className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

              <button type="submit" disabled={loading} className="btn-navy w-full disabled:opacity-60">
                {loading ? 'Sending OTP…' : 'Continue — Verify OTP'}
              </button>
            </form>

            <div className="mt-6 text-xs text-ink/60">
              Already have an account?{' '}
              <Link href="/login" className="font-semibold text-navy hover:underline">Sign in</Link>
            </div>
          </>
        ) : (
          <form onSubmit={verifyOtp} className="space-y-5">
            <div>
              <div className="font-display text-xl font-bold tracking-tight">Verify your account</div>
              <p className="mt-1 text-sm text-ink/60">
                {startRes?.delivery === 'email' ? (
                  <>We emailed a 6-digit code to <span className="font-medium">{startRes?.email}</span>. Enter it below.</>
                ) : (
                  <>Enter the code for <span className="font-medium">{startRes?.email}</span>.</>
                )}
              </p>
            </div>

            {startRes?.delivery === 'email' ? (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
                <div className="mono-label text-emerald-700">✉ Codes sent to your email</div>
                <p className="mt-1 font-mono text-[11px] text-emerald-800">
                  Check your inbox (and spam) for your verification code.
                </p>
              </div>
            ) : (
              startRes && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
                  <div className="mono-label text-amber-700">Demo mode — code auto-generated</div>
                  <div className="mt-2 font-mono text-sm text-amber-800">
                    Email code: <strong>{startRes.demo_email_otp}</strong>
                  </div>
                </div>
              )
            )}

            <label className="block">
              <span className="mono-label mb-2 block">Email Verification Code</span>
              <input
                value={emailOtp}
                onChange={(e) => setEmailOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                inputMode="numeric"
                placeholder="6-digit code"
                className="input text-center text-xl tracking-[0.4em]"
              />
            </label>

            {error && <div className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

            <button type="submit" disabled={loading || emailOtp.length < 6} className="btn-navy w-full disabled:opacity-60">
              {loading ? 'Verifying…' : 'Verify & Create Account'}
            </button>

            <div className="flex items-center justify-between text-xs text-ink/60">
              <button type="button" onClick={() => setStep('details')} className="hover:text-navy">← Edit details</button>
              <button type="button" onClick={resend} className="font-semibold text-navy hover:underline">Resend code</button>
            </div>
          </form>
        )}
      </div>
    </section>
  );
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  required,
  placeholder,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
  placeholder?: string;
  hint?: string;
}) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} required={required} placeholder={placeholder} className="input" />
      {hint && <span className="mt-1 block font-mono text-[10px] text-ink/40">{hint}</span>}
    </label>
  );
}

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-bone">
      <SiteHeader />
      <Suspense fallback={<div className="container-x py-20 font-mono text-sm text-ink/50">Loading…</div>}>
        <RegisterForm />
      </Suspense>
    </div>
  );
}

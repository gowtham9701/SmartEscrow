'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import type { User } from '@/lib/types';

const SIZES = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'];
const INDUSTRIES = ['Technology', 'Financial Technology', 'SaaS / Enterprise', 'HealthTech', 'E-commerce', 'Global Capability Center', 'Consulting', 'Other'];

export function FirmRegisterModal({
  open,
  onClose,
  onVerified,
}: {
  open: boolean;
  onClose: () => void;
  onVerified: (user: User) => void;
}) {
  const { setUser } = useAuth();
  const [firmName, setFirmName] = useState('');
  const [regNumber, setRegNumber] = useState('');
  const [workEmail, setWorkEmail] = useState('');
  const [website, setWebsite] = useState('');
  const [size, setSize] = useState('11-50');
  const [industry, setIndustry] = useState('Technology');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [verified, setVerified] = useState(false);

  if (!open) return null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const user = await api.registerFirm({
        firm_name: firmName,
        firm_reg_number: regNumber,
        firm_work_email: workEmail,
        website,
        company_size: size,
        industry,
      });
      setUser(user);
      setVerified(true);
      setTimeout(() => {
        onVerified(user);
        onClose();
      }, 1400);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-coal/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg overflow-hidden rounded-2xl bg-surface shadow-2xl">
        <div className="flex items-center justify-between bg-navy px-6 py-4 text-paper">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em]">🏢 Register Your Firm</span>
          <button onClick={onClose} className="font-mono text-lg leading-none text-paper/70 hover:text-paper">×</button>
        </div>

        <div className="p-6 md:p-8">
          {verified ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-500/25 text-3xl text-emerald-600 dark:text-emerald-300">✓</div>
              <div className="mt-5 font-display text-2xl font-bold tracking-tight">Firm Verified</div>
              <p className="mt-2 text-sm text-ink/60">Employer rights unlocked. Switching to employer mode…</p>
            </div>
          ) : (
            <>
              <p className="text-sm text-ink/70">
                Employer rights require a verified business. Provide your firm details below to unlock posting jobs and hiring talent.
              </p>
              <form onSubmit={submit} className="mt-6 space-y-4">
                <Field label="Company / Firm Name" value={firmName} onChange={setFirmName} required placeholder="Acme Technologies Pvt Ltd" />
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Business Reg. Number" value={regNumber} onChange={setRegNumber} required placeholder="REG-123456 / CIN / GST" />
                  <Field label="Work Email" type="email" value={workEmail} onChange={setWorkEmail} required placeholder="you@company.com" />
                </div>
                <Field label="Website" value={website} onChange={setWebsite} placeholder="https://company.com" />
                <div className="grid gap-4 sm:grid-cols-2">
                  <Select label="Company Size" value={size} onChange={setSize} options={SIZES} />
                  <Select label="Industry" value={industry} onChange={setIndustry} options={INDUSTRIES} />
                </div>

                {error && <div className="rounded-xl border border-rose-300 dark:border-rose-500/40 bg-rose-50 dark:bg-rose-500/15 px-3 py-2 text-sm text-rose-700 dark:text-rose-200">{error}</div>}

                <button type="submit" disabled={loading} className="btn-navy w-full disabled:opacity-60">
                  {loading ? 'Verifying firm…' : 'Verify & Unlock Employer Rights'}
                </button>
                <p className="text-center font-mono text-[10px] text-ink/40">
                  Demo verification is instant. In production this would validate your registration number against a business registry.
                </p>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', required, placeholder }: { label: string; value: string; onChange: (v: string) => void; type?: string; required?: boolean; placeholder?: string }) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} required={required} placeholder={placeholder} className="input" />
    </label>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="input">
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}

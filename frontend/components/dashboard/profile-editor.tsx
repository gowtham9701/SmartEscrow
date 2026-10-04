'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { SkillChips } from '@/components/ui';

export function ProfileEditor() {
  const { user, setUser } = useAuth();
  const isClient = user?.role === 'client';

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [title, setTitle] = useState(user?.title || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [location, setLocation] = useState(user?.location || '');
  const [rate, setRate] = useState(user?.hourly_rate_usd || 60);
  const [years, setYears] = useState(user?.years_experience || 1);
  const [availability, setAvailability] = useState(user?.availability || 'available');
  const [github, setGithub] = useState(user?.github_username || '');
  const [skills, setSkills] = useState((user?.skills || []).join(', '));
  const [achievements, setAchievements] = useState((user?.achievements || []).join('\n'));
  const [services, setServices] = useState(
    (user?.services || []).map((s) => `${s.title} | ${s.rate}`).join('\n'),
  );

  // client fields
  const [company, setCompany] = useState(user?.company_name || '');
  const [industry, setIndustry] = useState(user?.industry || '');
  const [website, setWebsite] = useState(user?.website || '');
  const [companySize, setCompanySize] = useState(user?.company_size || '1-10');

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  const parsedSkills = skills.split(',').map((s) => s.trim()).filter(Boolean);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    setError('');
    try {
      const payload: Record<string, unknown> = {
        full_name: fullName,
        bio,
        location,
        skills: parsedSkills,
      };
      if (isClient) {
        Object.assign(payload, {
          company_name: company,
          industry,
          website,
          company_size: companySize,
        });
      } else {
        Object.assign(payload, {
          title,
          hourly_rate_usd: Number(rate),
          years_experience: Number(years),
          availability,
          github_username: github,
          achievements: achievements.split('\n').map((a) => a.trim()).filter(Boolean),
          services: services
            .split('\n')
            .map((line) => {
              const [t, r] = line.split('|').map((x) => x.trim());
              return t ? { title: t, rate: Number(r) || Number(rate) } : null;
            })
            .filter(Boolean),
        });
      }
      const updated = await api.updateProfile(payload);
      setUser(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={save} className="grid gap-8 lg:grid-cols-[1.5fr_1fr]">
      <div className="card space-y-5 p-8">
        <div className="font-display text-xl font-bold tracking-tight">Edit Profile</div>

        <Field label="Full Name" value={fullName} onChange={setFullName} />

        {isClient ? (
          <>
            <Field label="Company Name" value={company} onChange={setCompany} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Industry" value={industry} onChange={setIndustry} />
              <Field label="Company Size" value={companySize} onChange={setCompanySize} />
            </div>
            <Field label="Website" value={website} onChange={setWebsite} placeholder="https://" />
          </>
        ) : (
          <>
            <Field label="Professional Title" value={title} onChange={setTitle} />
            <div className="grid gap-4 sm:grid-cols-3">
              <NumberField label="Hourly Rate ($)" value={rate} onChange={setRate} />
              <NumberField label="Years Exp." value={years} onChange={setYears} />
              <label className="block">
                <span className="mono-label mb-2 block">Availability</span>
                <select value={availability} onChange={(e) => setAvailability(e.target.value)} className="input">
                  <option value="available">Available</option>
                  <option value="limited">Limited</option>
                  <option value="unavailable">Unavailable</option>
                </select>
              </label>
            </div>
            <Field label="GitHub Username" value={github} onChange={setGithub} placeholder="octocat" />
          </>
        )}

        <Field label="Location" value={location} onChange={setLocation} />

        <label className="block">
          <span className="mono-label mb-2 block">Bio</span>
          <textarea value={bio} onChange={(e) => setBio(e.target.value)} className="input min-h-[120px]" />
        </label>

        <Field label={isClient ? 'Focus Areas (comma-separated)' : 'Skills (comma-separated)'} value={skills} onChange={setSkills} placeholder="Python, React, AWS" />

        {!isClient && (
          <>
            <label className="block">
              <span className="mono-label mb-2 block">Achievements (one per line)</span>
              <textarea value={achievements} onChange={(e) => setAchievements(e.target.value)} className="input min-h-[90px]" placeholder={'AWS Certified\nTop 1% reviewer'} />
            </label>
            <label className="block">
              <span className="mono-label mb-2 block">Service Rates (Title | $rate, one per line)</span>
              <textarea value={services} onChange={(e) => setServices(e.target.value)} className="input min-h-[90px]" placeholder={'Backend architecture | 120\nUI build | 95'} />
            </label>
          </>
        )}

        {error && <div className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {saved && <div className="rounded-xl border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">Profile saved.</div>}

        <button type="submit" disabled={saving} className="btn-navy w-full disabled:opacity-60">
          {saving ? 'Saving…' : 'Save Profile'}
        </button>
      </div>

      {/* Live preview */}
      <aside className="lg:sticky lg:top-24 lg:self-start">
        <div className="card p-6">
          <div className="mono-label">Live Preview</div>
          <div className="mt-4 font-display text-xl font-bold tracking-tight">
            {fullName || 'Your Name'}
          </div>
          <div className="font-mono text-xs text-ink/50">{isClient ? company || 'Company' : title || 'Title'}</div>
          {!isClient && (
            <div className="mt-3 font-display text-2xl font-bold">
              ${rate}
              <span className="font-sans text-xs font-normal text-ink/50">/hr</span>
            </div>
          )}
          <p className="mt-3 text-sm text-ink/70">{bio || 'Your bio will appear here.'}</p>
          {parsedSkills.length > 0 && (
            <div className="mt-4">
              <SkillChips skills={parsedSkills} max={12} />
            </div>
          )}
        </div>
      </aside>
    </form>
  );
}

function Field({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="input" />
    </label>
  );
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="block">
      <span className="mono-label mb-2 block">{label}</span>
      <input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} className="input" />
    </label>
  );
}

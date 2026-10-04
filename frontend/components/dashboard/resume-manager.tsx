'use client';

import { useRef, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { SkillChips, MatchBadge } from '@/components/ui';
import type { ResumeAnalysis } from '@/lib/types';

export function ResumeManager() {
  const { user, setUser } = useAuth();
  const fileRef = useRef<HTMLInputElement>(null);
  const [resumeText, setResumeText] = useState(user?.resume_text || '');
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [fileName, setFileName] = useState(user?.resume_filename || '');

  const handleFile = async (file: File) => {
    setBusy(true);
    setError('');
    try {
      const res = await api.resumeUpload(file);
      setUser(res.user);
      setAnalysis(res.analysis);
      setResumeText(res.user.resume_text || '');
      setFileName(file.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setBusy(false);
    }
  };

  const analyzeText = async () => {
    if (resumeText.trim().length < 20) {
      setError('Please paste at least a few lines of your resume.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const res = await api.resumeText(resumeText, fileName || 'resume.txt');
      setUser(res.user);
      setAnalysis(res.analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setBusy(false);
    }
  };

  const hasResume = Boolean(user?.resume_text || user?.resume_url);

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div className="mono-label text-accent">📄 Resume & AI Skill Analysis</div>
          {hasResume ? (
            <span className="font-mono text-[10px] text-emerald-600 dark:text-emerald-300">✓ On file{fileName ? ` · ${fileName}` : ''}</span>
          ) : (
            <span className="font-mono text-[10px] text-amber-600 dark:text-amber-300">Required to apply for jobs</span>
          )}
        </div>
        <p className="mt-2 text-sm text-ink/60">
          Upload your resume (PDF, DOCX, or TXT) or paste the text. Our AI extracts your skills, matches you to open
          roles, and recommends in-demand skills to learn.
        </p>

        {/* Upload dropzone */}
        <div
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) handleFile(f);
          }}
          className="mt-5 cursor-pointer rounded-2xl border-2 border-dashed border-ink/20 p-8 text-center transition hover:border-navy"
        >
          <div className="text-3xl">⬆️</div>
          <div className="mt-2 font-display font-bold">Drop your resume here or click to upload</div>
          <div className="mt-1 font-mono text-[11px] text-ink/50">PDF · DOCX · TXT — max 5MB</div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
        </div>

        <div className="mt-5">
          <div className="mono-label mb-2">Or paste resume text</div>
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            className="input min-h-[140px]"
            placeholder="Paste your resume — summary, experience, skills, education…"
          />
        </div>

        {error && <div className="mt-4 rounded-xl border border-rose-300 dark:border-rose-500/40 bg-rose-50 dark:bg-rose-500/15 px-3 py-2 text-sm text-rose-700 dark:text-rose-200">{error}</div>}

        <button onClick={analyzeText} disabled={busy} className="btn-navy mt-5 w-full disabled:opacity-60">
          {busy ? 'Analyzing with AI…' : '✦ Analyze & Save Resume'}
        </button>
      </div>

      {analysis && <ResumeInsights analysis={analysis} />}
    </div>
  );
}

export function ResumeInsights({ analysis }: { analysis: ResumeAnalysis }) {
  if (analysis.has_resume === false) return null;
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-2 bg-navy px-6 py-3 text-paper">
        <span className="font-mono text-[11px] uppercase tracking-[0.18em]">✦ AI Resume Insights</span>
        <span className="ml-auto font-mono text-[10px] text-paper/60">
          {analysis.seniority}{analysis.years_experience ? ` · ${analysis.years_experience}y` : ''}
        </span>
      </div>
      <div className="p-6">
        {analysis.summary && <p className="text-sm italic text-ink/70">{analysis.summary}</p>}

        <div className="mono-label mt-5 text-accent">Extracted Skills</div>
        <div className="mt-2">
          <SkillChips skills={analysis.extracted_skills} max={20} />
        </div>

        {analysis.recommended_skills.length > 0 && (
          <>
            <div className="mono-label mt-5 text-accent">Recommended Skills to Learn</div>
            <p className="mb-2 mt-1 font-mono text-[11px] text-ink/50">In-demand across open roles — add these to boost your matches.</p>
            <div className="flex flex-wrap gap-2">
              {analysis.recommended_skills.map((s) => (
                <span key={s} className="rounded-full border border-amber-300 dark:border-amber-500/40 bg-amber-50 dark:bg-amber-500/15 px-3 py-1 font-mono text-[11px] uppercase tracking-wide text-amber-700 dark:text-amber-200">
                  + {s}
                </span>
              ))}
            </div>
          </>
        )}

        {analysis.top_matches.length > 0 && (
          <>
            <div className="mono-label mt-6 text-accent">Top Job Matches For You</div>
            <div className="mt-3 space-y-3">
              {analysis.top_matches.map((m) => (
                <a key={m.id} href={`/jobs/${m.id}`} className="block rounded-xl border border-ink/10 p-4 transition hover:shadow-md">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate font-display font-bold">{m.title}</div>
                      <div className="truncate font-mono text-xs text-ink/50">
                        {m.company_name} · ${m.hourly_rate_min}–${m.hourly_rate_max}/hr
                      </div>
                    </div>
                    <MatchBadge score={m.match_score} />
                  </div>
                  {m.missing_skills.length > 0 && (
                    <div className="mt-2 font-mono text-[11px] text-ink/50">
                      To improve: {m.missing_skills.join(', ')}
                    </div>
                  )}
                </a>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

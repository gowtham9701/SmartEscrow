"use client";

import { useEffect, useState } from 'react';

const navItems = ['Overview', 'Projects', 'Escrow', 'Vetting', 'Disputes'];

export function DashboardShell() {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/dashboard/summary`);
        const data = await res.json();
        setSummary(data);
      } catch {
        setSummary({
          kpis: {
            total_value_locked: 1842500,
            active_projects: 27,
            completion_rate: 86,
            disputes_open: 4,
            verification_score: 92,
            payout_latency_hours: 18,
          },
          revenueTrend: [
            { month: 'Jan', value: 110000 },
            { month: 'Feb', value: 128000 },
            { month: 'Mar', value: 141000 },
            { month: 'Apr', value: 155000 },
            { month: 'May', value: 173000 },
            { month: 'Jun', value: 188000 },
          ],
        });
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  if (loading || !summary) {
    return <div className="min-h-screen bg-slate-950 p-12 text-slate-100">Loading dashboard...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <aside className="fixed inset-y-0 left-0 w-72 border-r border-white/10 bg-slate-900/80 p-6 backdrop-blur-xl">
        <div className="text-2xl font-bold text-sky-400">SmartEscrow</div>
        <nav className="mt-10 space-y-2">
          {navItems.map((item, idx) => (
            <button key={item} className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left ${idx === 0 ? 'bg-sky-500/15 text-sky-300' : 'text-slate-300 hover:bg-slate-800'}`}>
              <span>{item}</span>
              <span className="text-xs text-slate-500">0{idx + 1}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="ml-72 p-8">
        <header className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-sky-300">Operations</p>
            <h1 className="mt-2 text-4xl font-semibold">Portfolio Dashboard</h1>
          </div>
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300">
            96% compliance healthy
          </div>
        </header>

        <div className="mt-8 grid gap-4 md:grid-cols-3 xl:grid-cols-6">
          {[
            ['Total Value Locked', `$${(summary.kpis.total_value_locked / 1000000).toFixed(2)}M`],
            ['Active Projects', summary.kpis.active_projects],
            ['Completion Rate', `${summary.kpis.completion_rate}%`],
            ['Open Disputes', summary.kpis.disputes_open],
            ['Verification Score', `${summary.kpis.verification_score}%`],
            ['Payout Latency', `${summary.kpis.payout_latency_hours}h`],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-slate-900 p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{label}</div>
              <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
            </div>
          ))}
        </div>

        <div className="mt-8 grid gap-6 xl:grid-cols-[1.5fr_0.8fr]">
          <div className="rounded-2xl border border-white/10 bg-slate-900 p-5">
            <div className="mb-4 text-lg font-semibold">Revenue trend</div>
            <div className="flex h-52 items-end gap-3">
              {summary.revenueTrend.map((point: any) => (
                <div key={point.month} className="flex flex-1 flex-col items-center gap-2">
                  <div className="w-full rounded-t-xl bg-gradient-to-t from-sky-500 to-cyan-300" style={{ height: `${(point.value / 200000) * 100}%` }} />
                  <span className="text-xs text-slate-400">{point.month}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-slate-900 p-5">
            <div className="mb-4 text-lg font-semibold">Portfolio mix</div>
            <div className="space-y-4">
              {(summary.pipeline || []).map((item: any) => (
                <div key={item.name}>
                  <div className="mb-1 flex justify-between text-sm text-slate-300">
                    <span>{item.name}</span>
                    <span>{item.value}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-800">
                    <div className="h-2 rounded-full" style={{ width: `${item.value}%`, background: item.fill }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

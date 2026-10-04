'use client';

import { useEffect, useState } from 'react';
import { api, formatUSD } from '@/lib/api';
import type { PlatformStats } from '@/lib/types';

export function HomeStats() {
  const [stats, setStats] = useState<PlatformStats | null>(null);

  useEffect(() => {
    api.stats().then(setStats).catch(() => setStats(null));
  }, []);

  const items = [
    { label: 'Open Roles', value: stats ? `${stats.open_jobs}` : '—' },
    { label: 'Vetted Contributors', value: stats ? `${stats.contributors}` : '—' },
    { label: 'Active Engagements', value: stats ? `${stats.active_engagements}` : '—' },
    { label: 'Paid Out', value: stats ? formatUSD(stats.total_paid_out) : '—' },
  ];

  return (
    <section className="container-x mt-10">
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-ink/10 bg-ink/10 md:grid-cols-4">
        {items.map((it) => (
          <div key={it.label} className="bg-surface p-8">
            <div className="font-display text-4xl font-bold tracking-tight">{it.value}</div>
            <div className="mono-label mt-2">{it.label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

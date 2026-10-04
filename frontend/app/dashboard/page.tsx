'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { DashboardClient } from '@/components/dashboard/dashboard-client';
import { SiteHeader } from '@/components/site-header';

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-bone">
        <SiteHeader />
        <div className="container-x py-20">
          <div className="h-10 w-1/3 animate-pulse rounded bg-ink/10" />
          <div className="mt-6 grid gap-4 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-2xl bg-ink/5" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return <DashboardClient />;
}

'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { useTheme } from '@/lib/theme-context';
import { FirmRegisterModal } from '@/components/firm-register-modal';

const NAV = [
  { href: '/jobs', label: 'Find Work' },
  { href: '/talent', label: 'Find Talent' },
  { href: '/how-it-works', label: 'How It Works' },
  { href: '/about', label: 'About' },
];

export function SiteHeader() {
  const { user, logout, setUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [firmOpen, setFirmOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const mode = user?.active_mode || (user?.role === 'client' ? 'employer' : 'freelancer');

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const switchMode = async (target: 'freelancer' | 'employer') => {
    if (!user || switching || mode === target) return;
    setSwitching(true);
    try {
      const res = await api.switchMode(target);
      if (res.needs_firm) {
        setFirmOpen(true);
      } else {
        setUser(res.user);
        router.push('/dashboard');
      }
    } catch {
      /* ignore */
    } finally {
      setSwitching(false);
      setMenuOpen(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 border-b border-ink/10 bg-bone/85 backdrop-blur">
      <div className="container-x flex h-20 items-center justify-between">
        <Link href="/" className="font-display text-lg font-bold tracking-tight">
          Smart<span className="text-navy dark:text-sky-300">Escrow</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`font-mono text-[12px] uppercase tracking-[0.12em] transition hover:text-navy dark:hover:text-sky-300 ${
                pathname.startsWith(item.href) ? 'text-navy dark:text-sky-300' : 'text-ink/70'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="flex h-10 w-10 items-center justify-center rounded-full border border-ink/20 text-ink/70 transition hover:border-ink hover:text-ink"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>

          {user ? (
            <>
              <div className="flex items-center rounded-full border border-ink/15 bg-surface p-1">
                {(['freelancer', 'employer'] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => switchMode(m)}
                    disabled={switching}
                    className={`rounded-full px-3 py-1.5 font-mono text-[10px] uppercase tracking-wide transition ${
                      mode === m ? 'bg-navy text-paper' : 'text-ink/50 hover:text-ink'
                    }`}
                  >
                    {m === 'freelancer' ? 'Freelancer' : 'Employer'}
                  </button>
                ))}
              </div>

              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex h-10 items-center gap-2 rounded-full border border-ink/20 px-3 text-ink/80 transition hover:border-ink"
                >
                  <span className="font-mono text-xs">{user.full_name.split(' ')[0]}</span>
                  <span className="text-[10px]">▾</span>
                </button>
                {menuOpen && (
                  <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-xl border border-ink/10 bg-surface shadow-xl">
                    <div className="border-b border-ink/10 px-4 py-3">
                      <div className="font-semibold">{user.full_name}</div>
                      <div className="font-mono text-[10px] text-ink/50">@{user.username} · {mode}</div>
                    </div>
                    <Link href="/dashboard" onClick={() => setMenuOpen(false)} className="block px-4 py-2.5 text-sm hover:bg-ink/5">Dashboard</Link>
                    <button onClick={toggleTheme} className="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-ink/5">
                      <span>Theme</span>
                      <span className="font-mono text-xs text-ink/60">{theme === 'dark' ? 'Dark 🌙' : 'Light ☀️'}</span>
                    </button>
                    <button onClick={() => { setMenuOpen(false); logout(); }} className="block w-full px-4 py-2.5 text-left text-sm text-rose-600 hover:bg-rose-50">Log out</button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link href="/login" className="font-mono text-[12px] uppercase tracking-[0.12em] text-ink/70 hover:text-navy">Login</Link>
              <Link href="/register" className="btn-navy py-2.5">Get Started</Link>
            </>
          )}
        </div>

        <button
          onClick={() => setOpen((v) => !v)}
          className="flex h-10 w-10 items-center justify-center rounded-full border border-ink/20 md:hidden"
          aria-label="Menu"
        >
          <span className="font-mono text-sm">{open ? '×' : '≡'}</span>
        </button>
      </div>

      {open && (
        <div className="border-t border-ink/10 bg-bone px-6 py-4 md:hidden">
          <div className="flex flex-col gap-3">
            {NAV.map((item) => (
              <Link key={item.href} href={item.href} onClick={() => setOpen(false)} className="font-mono text-xs uppercase tracking-[0.12em] text-ink/70">
                {item.label}
              </Link>
            ))}
            <button onClick={toggleTheme} className="text-left font-mono text-xs uppercase tracking-[0.12em] text-ink/70">
              Theme: {theme === 'dark' ? 'Dark 🌙' : 'Light ☀️'}
            </button>
            {user ? (
              <>
                <div className="flex items-center rounded-full border border-ink/15 bg-surface p-1">
                  {(['freelancer', 'employer'] as const).map((m) => (
                    <button key={m} onClick={() => switchMode(m)} className={`flex-1 rounded-full px-3 py-1.5 font-mono text-[10px] uppercase tracking-wide ${mode === m ? 'bg-navy text-paper' : 'text-ink/50'}`}>
                      {m}
                    </button>
                  ))}
                </div>
                <Link href="/dashboard" onClick={() => setOpen(false)} className="font-mono text-xs uppercase tracking-[0.12em] text-navy">Dashboard</Link>
                <button onClick={logout} className="btn-outline mt-2 w-full">Log out</button>
              </>
            ) : (
              <div className="mt-2 flex gap-3">
                <Link href="/login" onClick={() => setOpen(false)} className="btn-outline flex-1">Login</Link>
                <Link href="/register" onClick={() => setOpen(false)} className="btn-navy flex-1">Get Started</Link>
              </div>
            )}
          </div>
        </div>
      )}

      <FirmRegisterModal
        open={firmOpen}
        onClose={() => setFirmOpen(false)}
        onVerified={(u) => { setUser(u); router.push('/dashboard'); }}
      />
    </header>
  );
}

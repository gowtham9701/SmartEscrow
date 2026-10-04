import Link from 'next/link';

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-ink/10 bg-coal text-paper">
      <div className="container-x py-16">
        <div className="grid gap-12 md:grid-cols-[2fr_1fr_1fr_1fr]">
          <div>
            <div className="font-display text-2xl font-bold tracking-tight">
              SmartEscrow
            </div>
            <p className="mt-4 max-w-sm text-sm text-paper/60">
              Algorithmic B2B infrastructure for tech talent. AI-vetted contributors,
              hourly engagements, and automated USD escrow — zero predatory fees.
            </p>
          </div>

          <FooterCol
            title="Platform"
            links={[
              { href: '/jobs', label: 'Find Work' },
              { href: '/talent', label: 'Find Talent' },
              { href: '/register', label: 'Get Started' },
            ]}
          />
          <FooterCol
            title="Company"
            links={[
              { href: '/about', label: 'About' },
              { href: '/how-it-works', label: 'How It Works' },
              { href: '/contact', label: 'Contact' },
            ]}
          />
          <FooterCol
            title="Account"
            links={[
              { href: '/login', label: 'Login' },
              { href: '/dashboard', label: 'Dashboard' },
            ]}
          />
        </div>

        <div className="mt-14 flex flex-col items-start justify-between gap-4 border-t border-paper/15 pt-8 text-xs text-paper/50 md:flex-row md:items-center">
          <span className="font-mono uppercase tracking-[0.12em]">
            © {new Date().getFullYear()} SmartEscrow. All rights reserved.
          </span>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: { href: string; label: string }[] }) {
  return (
    <div>
      <div className="mono-label text-paper/50">{title}</div>
      <ul className="mt-4 space-y-2 text-sm">
        {links.map((l) => (
          <li key={l.href}>
            <Link href={l.href} className="text-paper/80 transition hover:text-paper">
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

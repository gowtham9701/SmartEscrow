import type { Config } from 'tailwindcss';

const withVar = (v: string) => `rgb(var(${v}) / <alpha-value>)`;

const config: Config = {
  darkMode: 'class',
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}', './components/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        // Neutral tokens that adapt between light and dark themes.
        bone: withVar('--c-bone'),
        surface: withVar('--c-surface'),
        ink: withVar('--c-ink'),
        sand: withVar('--c-sand'),
        // Fixed tokens.
        paper: '#f4f2ee', // near-white: light text on dark/brand surfaces
        coal: '#0d1117', // always-dark surfaces (footer, table headers, cards on brand)
        navy: {
          DEFAULT: '#1d2a44',
          900: '#161f33',
          700: '#263554',
        },
        accent: '#c8502d',
      },
      fontFamily: {
        display: ['var(--font-display)', 'Arial Black', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
      },
      letterSpacing: {
        tightest: '-0.04em',
      },
      maxWidth: {
        container: '1280px',
      },
    },
  },
  plugins: [],
};

export default config;

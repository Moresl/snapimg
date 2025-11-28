import { defineConfig, presetUno, presetIcons } from 'unocss'

export default defineConfig({
  presets: [
    presetUno({
      dark: 'class',
    }),
    presetIcons({
      scale: 1.2,
      cdn: 'https://esm.sh/',
    }),
  ],
  theme: {
    colors: {
      border: 'var(--border)',
      input: 'var(--input)',
      ring: 'var(--ring)',
      background: 'var(--background)',
      foreground: 'var(--foreground)',
      primary: {
        DEFAULT: 'var(--primary)',
        foreground: 'var(--primary-foreground)',
      },
      secondary: {
        DEFAULT: 'var(--secondary)',
        foreground: 'var(--secondary-foreground)',
      },
      destructive: {
        DEFAULT: 'var(--destructive)',
        foreground: 'var(--destructive-foreground)',
      },
      muted: {
        DEFAULT: 'var(--muted)',
        foreground: 'var(--muted-foreground)',
      },
      accent: {
        DEFAULT: 'var(--accent)',
        foreground: 'var(--accent-foreground)',
      },
      success: {
        DEFAULT: 'var(--success)',
        foreground: 'var(--success-foreground)',
      },
      card: {
        DEFAULT: 'var(--card)',
        foreground: 'var(--card-foreground)',
      },
    },
  },
  shortcuts: {
    'btn': 'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
    'btn-primary': 'btn bg-primary text-primary-foreground hover:bg-primary/90',
    'btn-secondary': 'btn bg-secondary text-secondary-foreground hover:bg-secondary/80',
    'btn-destructive': 'btn bg-destructive text-destructive-foreground hover:bg-destructive/90',
    'btn-outline': 'btn border border-border bg-background hover:bg-accent hover:text-accent-foreground',
    'btn-ghost': 'btn hover:bg-accent hover:text-accent-foreground',
    'btn-success': 'btn bg-success text-success-foreground hover:bg-success/90',
    'btn-lg': 'h-10 px-6 rounded-lg',
    'btn-sm': 'h-8 px-3 text-xs rounded-lg',
    'btn-icon': 'h-9 w-9 rounded-lg',
    'card': 'rounded-2xl border bg-card text-card-foreground shadow-sm',
    'card-content': 'p-4',
    'badge': 'inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold',
    'badge-success': 'badge border-success/20 bg-success/10 text-success',
    'input': 'flex h-10 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50',
  },
})

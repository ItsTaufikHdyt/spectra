/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Token desain Digital Twin Bontang: nilai per tema (terang/gelap) ada di CSS variable `--bontang-*`
      // (src/assets/main.css). Kontras teks diuji WCAG AA (>= 4,5:1); jangan pakai `subtle` untuk teks < 12 px.
      colors: {
        bontang: {
          'ink': 'rgb(var(--bontang-ink) / <alpha-value>)',
          'panel': 'rgb(var(--bontang-panel) / <alpha-value>)',
          'raised': 'rgb(var(--bontang-raised) / <alpha-value>)',
          'line': 'rgb(var(--bontang-line) / <alpha-value>)',
          'edge': 'rgb(var(--bontang-edge) / <alpha-value>)',
          'text': 'rgb(var(--bontang-text) / <alpha-value>)',
          'muted': 'rgb(var(--bontang-muted) / <alpha-value>)',
          'subtle': 'rgb(var(--bontang-subtle) / <alpha-value>)',
          'accent': 'rgb(var(--bontang-accent) / <alpha-value>)',
          'accent-ink': 'rgb(var(--bontang-accent-ink) / <alpha-value>)',
          'danger': 'rgb(var(--bontang-danger) / <alpha-value>)',
          'ok': 'rgb(var(--bontang-ok) / <alpha-value>)',
          'warn': 'rgb(var(--bontang-warn) / <alpha-value>)'
        }
      },
      fontFamily: {
        sans: ['"Public Sans"', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif']
      },
      fontSize: {
        caption: ['11px', '16px'],
        small: ['12px', '18px'],
        body: ['13px', '20px'],
        title: ['15px', '22px'],
        display: ['17px', '24px']
      }
    }
  },
  plugins: []
};

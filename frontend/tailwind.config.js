/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Token desain Digital Twin Bontang. Kontras teks diuji terhadap WCAG AA (>= 4,5:1)
      // pada ink/panel/raised; jangan pakai `subtle` untuk teks di bawah 12 px.
      colors: {
        bontang: {
          ink: '#0D1820', // latar aplikasi
          panel: '#122230', // panel kiri/kanan, header
          raised: '#19303F', // kartu, kontrol aktif
          line: '#284556', // garis pemisah (dekoratif)
          edge: '#557688', // batas kontrol interaktif (>= 3:1)
          text: '#E4ECF0',
          muted: '#9DB2BE',
          subtle: '#869EAC',
          accent: '#F0B43C', // amber "pelampung": satu-satunya aksen UI
          'accent-ink': '#1A1203', // teks di atas aksen
          danger: '#F08A7E',
          ok: '#7FD1A8'
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

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bontang: {
          dark: '#0f172a',
          card: '#1e293b',
          accent: '#38bdf8',
          border: '#334155'
        }
      }
    },
  },
  plugins: [],
}

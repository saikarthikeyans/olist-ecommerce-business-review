/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
          600: '#475569',
        },
        brand: {
          blue: '#2563eb',
          amber: '#d97706',
          emerald: '#059669',
          rose: '#e11d48',
        }
      }
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sand: {
          50: '#FDFBF7',
          100: '#F7F4EE',
          200: '#EBE5D9',
          300: '#DDD4C4',
          400: '#C2B49D',
          500: '#A49378',
          600: '#85735B',
          700: '#685844',
          800: '#4F4233',
          900: '#382F24',
        },
        warm: {
          surface: '#FAF8F5',
          card: '#FFFFFF',
          border: '#E8E3DA',
          muted: '#78716C',
          dark: '#1C1917',
          accent: '#D97706', // Amber accent
          emerald: '#059669',
          rose: '#E11D48',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'sans-serif'],
        serif: ['Newsreader', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'warm-sm': '0 1px 3px 0 rgba(40, 30, 20, 0.04), 0 1px 2px -1px rgba(40, 30, 20, 0.04)',
        'warm-md': '0 4px 12px -2px rgba(40, 30, 20, 0.06), 0 2px 6px -2px rgba(40, 30, 20, 0.04)',
        'warm-lg': '0 10px 25px -5px rgba(40, 30, 20, 0.08), 0 8px 10px -6px rgba(40, 30, 20, 0.04)',
      }
    },
  },
  plugins: [],
}

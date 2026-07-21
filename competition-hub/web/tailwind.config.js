/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#05070f',
          900: '#080b16',
          850: '#0b1020',
          800: '#0f1626',
          700: '#16203a',
          600: '#1f2c4d',
        },
        neon: {
          cyan: '#22d3ee',
          blue: '#38bdf8',
          violet: '#a855f7',
          pink: '#ec4899',
          green: '#34d399',
          amber: '#fbbf24',
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 24px rgba(34,211,238,0.25)',
        'glow-violet': '0 0 24px rgba(168,85,247,0.28)',
      },
      keyframes: {
        floaty: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-6px)' } },
        pulseGlow: { '0%,100%': { opacity: '0.6' }, '50%': { opacity: '1' } },
      },
      animation: {
        floaty: 'floaty 4s ease-in-out infinite',
        pulseGlow: 'pulseGlow 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}

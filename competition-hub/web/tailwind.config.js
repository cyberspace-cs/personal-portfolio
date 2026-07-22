/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0b1020',
          900: '#0f1628',
          850: '#141d33',
          800: '#1b2742',
          700: '#26344f',
          600: '#324264',
        },
        neon: {
          cyan: '#22d3ee',
          blue: '#38bdf8',
          teal: '#2dd4bf',
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
        glow: '0 0 28px rgba(34,211,238,0.30)',
        'glow-cyan': '0 0 34px rgba(34,211,238,0.38)',
        'glow-violet': '0 0 28px rgba(168,85,247,0.32)',
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

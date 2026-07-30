/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0a1024',
          900: '#0d1530',
          850: '#111c3c',
          800: '#182548',
          700: '#22345e',
          600: '#2e4470',
        },
        neon: {
          cyan: '#38bdf8',
          blue: '#3b82f6',
          azure: '#60a5fa',
          ice: '#bae6fd',
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
        glow: '0 0 28px rgba(59,130,246,0.30)',
        'glow-blue': '0 0 34px rgba(59,130,246,0.42)',
        'glow-violet': '0 0 28px rgba(96,165,250,0.30)',
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

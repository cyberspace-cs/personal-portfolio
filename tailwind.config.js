export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'slate': {
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
          400: '#94a3b8',
          100: '#f1f5f9',
        },
        'sky': {
          400: '#38bdf8',
        },
        'indigo': {
          400: '#818cf8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}

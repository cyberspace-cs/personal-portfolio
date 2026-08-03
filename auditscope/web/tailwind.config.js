/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: { 900: '#0B1220', 800: '#111a2e', 700: '#1a2740' },
        brand: {
          primary: '#2563EB', accent: '#06B6D4',
          success: '#10B981', warning: '#F59E0B', danger: '#EF4444',
        },
        line: '#1E293B',
      },
      fontFamily: {
        sans: ['Inter', 'PingFang SC', 'Microsoft YaHei', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(37,99,235,.35), 0 8px 30px rgba(37,99,235,.15)',
      },
      keyframes: {
        shimmer: { '100%': { transform: 'translateX(100%)' } },
        fadeup: { '0%': { opacity: 0, transform: 'translateY(8px)' }, '100%': { opacity: 1, transform: 'none' } },
      },
      animation: { shimmer: 'shimmer 1.4s infinite', fadeup: 'fadeup .3s ease-out' },
    },
  },
  plugins: [],
}

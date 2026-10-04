/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#090a0f',
        surface: {
          50: '#1e212b',
          100: '#181b24',
          200: '#13151c',
          300: '#0e1017',
          400: '#090a0f',
        },
        border: 'rgba(255, 255, 255, 0.08)',
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 24px -4px rgba(99, 102, 241, 0.25)',
        'glow-cyan': '0 0 24px -4px rgba(6, 182, 212, 0.25)',
        'glow-emerald': '0 0 24px -4px rgba(16, 185, 129, 0.25)',
      },
    },
  },
  plugins: [],
}

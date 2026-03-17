/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        hydro: {
          50: '#eff8ff',
          100: '#dbeefe',
          200: '#bfe0fe',
          300: '#93ccfd',
          400: '#60b0fa',
          500: '#3b8ff5',
          600: '#2570ea',
          700: '#1d5bd7',
          800: '#1e4aae',
          900: '#1e4089',
        },
      },
    },
  },
  plugins: [],
};

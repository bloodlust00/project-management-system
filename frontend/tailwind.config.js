/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enables dark-mode toggle support
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f7ff',
          100: '#ebf0ff',
          200: '#d6e0ff',
          300: '#b3c7ff',
          400: '#85a3ff',
          500: '#5277ff', // Accent Indigo/Violet
          600: '#2e4eff',
          700: '#1d37e6',
          800: '#192dbb',
          900: '#192b95',
          950: '#0f1757',
        },
        dark: {
          50: '#f6f6f7',
          100: '#e1e1e4',
          200: '#c2c2c9',
          300: '#9b9ba4',
          400: '#72727c',
          500: '#565660',
          600: '#41414b',
          700: '#2a2a32',
          800: '#1e1e24',
          900: '#121216', // Slate dark BG
          950: '#0b0b0d',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        premium: '0 8px 30px rgb(0, 0, 0, 0.12)',
        glass: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
      },
      backdropBlur: {
        premium: '8px',
      }
    },
  },
  plugins: [],
}

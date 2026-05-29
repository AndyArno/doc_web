import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#E6F2FF',
          100: '#CCE5FF',
          200: '#99CCFF',
          300: '#66B2FF',
          400: '#3399FF',
          500: '#0088FF',
          600: '#0077E6',
          700: '#0066CC',
          800: '#0055B3',
          900: '#004499',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'brand': '0 2px 8px rgba(0, 136, 255, 0.25)',
        'brand-lg': '0 4px 16px rgba(0, 136, 255, 0.3)',
      },
    },
  },
  plugins: [],
}

export default config

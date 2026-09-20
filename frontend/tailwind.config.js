/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#05070d',
          900: '#0b0f1a',
          800: '#121826',
          750: '#161d2e',
          700: '#1c2438',
          line: '#253150',
          'line-soft': '#1a2338',
        },
        cnc: {
          blue: '#2e6ff2',
          'blue-glow': 'rgba(46, 111, 242, 0.25)',
          amber: '#ffb020',
          emerald: '#34d399',
          rose: '#f87171',
          sky: '#38bdf8',
        }
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

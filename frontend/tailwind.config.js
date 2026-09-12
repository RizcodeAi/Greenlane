/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f4f8', 100: '#d9e2ec', 200: '#bcccdc',
          300: '#9fb3c8', 400: '#829ab1', 500: '#627d98',
          600: '#486581', 700: '#334e68', 800: '#243b53',
          900: '#1a3a5c', 950: '#102a43',
        },
        green: { 500: '#16a34a', 600: '#15803d', 700: '#166534' },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

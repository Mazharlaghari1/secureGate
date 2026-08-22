/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        indigo: {
          650: '#4a44e0',
          655: '#433be5',
          750: '#3b32c0',
          755: '#3229a9',
        },
        slate: {
          450: '#7c8ba1',
          550: '#55657e',
        }
      }
    },
  },
  plugins: [],
}

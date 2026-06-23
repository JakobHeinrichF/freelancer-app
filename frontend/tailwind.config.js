/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        gs: {
          blue: '#3C5064',
          teal: '#DCE6E6',
          accent: '#5B8FA8',
        }
      }
    },
  },
  plugins: [],
}

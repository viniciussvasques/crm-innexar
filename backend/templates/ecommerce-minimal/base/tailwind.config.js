/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '{{PRIMARY_COLOR}}',
          dark: '{{PRIMARY_COLOR_DARK}}',
        },
        secondary: {
          DEFAULT: '{{SECONDARY_COLOR}}',
          dark: '{{SECONDARY_COLOR_DARK}}',
        },
        accent: {
          DEFAULT: '{{ACCENT_COLOR}}',
        },
      },
    },
  },
  plugins: [],
}

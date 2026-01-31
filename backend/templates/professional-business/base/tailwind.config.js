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
                    light: '{{PRIMARY_COLOR_LIGHT}}', // Need to calculate this one
                },
                secondary: {
                    DEFAULT: '{{SECONDARY_COLOR}}',
                    dark: '{{SECONDARY_COLOR_DARK}}',
                },
                accent: '{{ACCENT_COLOR}}',
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-conic':
                    'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
            },
        },
    },
    plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        githubBg: '#0d1117',
        githubCard: '#161b22',
        githubBorder: '#30363d',
        githubPrimary: '#2ea043',
        githubTextPrimary: '#c9d1d9',
        githubTextSecondary: '#8b949e',
      }
    },
  },
  plugins: [],
}
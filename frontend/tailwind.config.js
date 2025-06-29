/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        'topic': '#d946ef',     // magenta for topics
        'thought': '#22c55e',   // green for thoughts  
        'quote': '#eab308',     // yellow for quotes
        'passage': '#3b82f6',   // blue for passages
      }
    },
  },
  plugins: [],
}
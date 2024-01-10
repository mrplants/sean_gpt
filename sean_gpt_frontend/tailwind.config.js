/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js}"],
  theme: {
    extend: {
      wordBreak: ['break-word']
    },
  },
  plugins: [require("@tailwindcss/typography"), require("daisyui")],
}
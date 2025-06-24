/** @type {import('tailwindcss').Config} */
const colors = require('tailwindcss/colors')

module.exports = {
  content: ["./templates/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        teal: colors.teal,
        cyan: colors.cyan,
      },
      backgroundImage: {
        'fundo': "url('/static/Rectangle 1.jpg')",
        'cel_fun': "url('/static/Rectangle 1 (1).jpg')"
      },
  },
  plugins: [require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),]
  } 
}

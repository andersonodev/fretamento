/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#FAF9F6",
        accent: {
          sage: "#A3B18A",
          sand: "#DAD2BC",
          clay: "#B08968",
        },
        ink: "#333333",
      },
      fontFamily: {
        serif: ['"Playfair Display"', "serif"],
        sans: ['Inter', "sans-serif"],
      },
      boxShadow: {
        soft: "0 10px 30px rgba(0, 0, 0, 0.08)",
      },
    },
  },
  plugins: [],
};

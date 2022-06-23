module.exports = {
  plugins: [require('@tailwindcss/forms')],
  content: ["./templates/**/*.html", "./src/styles.css", "./src/**/*.jsx"],
  theme: {
    extend: {
      colors: {
        powder: {
          default: "#E7EAF9",
          light: "#F3F5FB",
          dark: "#CED5F2",
          darker: "#B8BFDA",
        },
        planitor: {
          blue: "#002EC2",
          darkBlue: "#0D2475",
          gold: "#755600",
          red: "#A33417",
          gray: "#dddedd",
          green: "#0c7556",
        },
      },
    },
  },
};

module.exports = {
  plugins: [],
  purge: false, // manually configured in postcss.config.js
  theme: {
    extend: {
      colors: {
        powder: {
          default: "#AAE0E3",
          light: "#D6F9F5",
          dark: "#8ADAE4",
          darker: "#46BCCC",
        },
        midnight: "#27226B",
      },
    },
  },
};

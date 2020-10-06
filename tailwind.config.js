module.exports = {
  plugins: [],
  future: {
    removeDeprecatedGapUtilities: true,
  },
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
        planitor: {
          blue: "#002EC2",
          darkBlue: "#0D2475",
          gold: "#755600",
          red: "#A33417",
          gray: "#dddedd",
        },
      },
    },
  },
};

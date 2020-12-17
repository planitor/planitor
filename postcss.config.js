// postcss.config.js
const purgecss = require("@fullhuman/postcss-purgecss")({
  // Specify the paths to all of the template files in your project
  content: ["./templates/**/*.html", "./src/styles.css", "./src/**/*.jsx"],

  // This is the function used to extract class names from your templates
  defaultExtractor: (content) => {
    // Capture as liberally as possible, including things like `h-(screen-1.5)`
    const broadMatches = content.match(/[^<>"'`\s]*[^<>"'`\s:]/g) || [];

    // Capture classes within other delimiters like .block(class="w-1/2") in Pug
    const innerMatches = content.match(/[^<>"'`\s.()]*[^<>"'`\s.():]/g) || [];

    return broadMatches.concat(innerMatches);
  },
});

module.exports = (context) => {
  return {
    plugins: [
      require("postcss-import"),
      require("tailwindcss"),
      require("postcss-preset-env")({
        stage: 2,
        features: {
          "focus-within-pseudo-class": false,
        },
      }),
      require("postcss-100vh-fix"),
      ...(process.env.NODE_ENV === "production"
        ? [purgecss, require("cssnano")]
        : []),
    ],
  };
};

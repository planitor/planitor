module.exports = {
  extends: "@snowpack/app-scripts-preact",
  plugins: ["@snowpack/plugin-postcss"],
  alias: { lodash: "lodash-es" },
};

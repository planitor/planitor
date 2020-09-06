import * as dotenv from "dotenv";
dotenv.config();

import postcss from "rollup-plugin-postcss";
import babel from "@rollup/plugin-babel";
import { terser } from "rollup-plugin-terser";
import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import replace from "@rollup/plugin-replace";

export default {
  input: "src/index.js",
  treeshake: true,
  output: {
    entryFileNames: "[name]-[hash].js",
    dir: "dist",
    format: "es",
    sourcemap: true,
    plugins: [terser()],
    manualChunks: (id) => {
      if (id.includes("node_modules")) {
        return "vendor";
      }
    },
  },
  plugins: [
    postcss({
      plugins: [],
      extract: true,
    }),
    babel({ babelHelpers: "bundled" }),
    resolve({ browser: true }),
    commonjs(),
    replace({
      __version__: process.env.VERSION,
      __sentryDsn__: process.env.SENTRY_DSN,
    }),
  ],
};

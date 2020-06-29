import "./styles.css";
import "./app.js";

// Hot Module Replacement (HMR) - Remove this snippet to remove HMR.
// Learn more: https://www.snowpack.dev/#hot-module-replacement
if (import.meta.hot && import.meta.env.MODE !== "development") {
  import.meta.hot.accept();
}

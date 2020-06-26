import { h, render } from "preact";
import "./styles.css";

const App = h("h1", null, "Hello World");

render(App, document.body);

// Hot Module Replacement (HMR) - Remove this snippet to remove HMR.
// Learn more: https://www.snowpack.dev/#hot-module-replacement
if (import.meta.hot) {
  import.meta.hot.accept();
}

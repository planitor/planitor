import { h, render } from "preact";

const App = () => h("h1", {}, "Hello from Preact and Typescript!");

render(<App />, document.getElementById("root"));

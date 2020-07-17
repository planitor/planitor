import { h, render } from "preact";

import "./maps";
import { Navigation } from "./navigation";

const navigationEl = document.getElementById("navigation");
if (navigationEl) {
  render(<Navigation />, navigationEl);
}

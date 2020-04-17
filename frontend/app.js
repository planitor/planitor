import { h, render } from "preact";

import "./maps";
import { Login } from "./accounts";
import { openModal } from "./modals";

document.getElementById("login").addEventListener("click", (event) => {
  event.stopPropagation();
  const el = openModal();
  render(<Login />, el);
});

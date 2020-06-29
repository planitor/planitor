import { h, render } from "preact";

import "./maps";
import { Login, NewPassword } from "./accounts";
import { openModal } from "./modals";

document.getElementById("login-button").addEventListener("click", (event) => {
  event.stopPropagation();
  const [el, cleanup] = openModal();
  render(<Login success={cleanup} />, el);
});

const passwordRecoveryEl = document.getElementById("password-recovery");
if (passwordRecoveryEl) {
  const el = openModal();
  render(<NewPassword token={passwordRecoveryEl.dataset.token} />, el);
}

const loginEl = document.getElementById("login");
if (loginEl) {
  const [el, close] = openModal();
  const cleanup = () => {
    window.location.pathname = loginEl.dataset.redirectTo;
  };
  render(<Login success={cleanup} />, el);
}

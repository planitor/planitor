import { h, render } from "preact";

import "./maps";
import { Login, NewPassword } from "./accounts";
import { openModal } from "./modals";
import { Navigation } from "./navigation";

const loginButtonEl = document.getElementById("login-button");

if (loginButtonEl) {
  loginButtonEl.addEventListener("click", (event) => {
    event.stopPropagation();
    const [el, cleanup] = openModal();
    render(<Login success={cleanup} />, el);
  });
}

const navigationEl = document.getElementById("navigation");
if (navigationEl) {
  render(<Navigation user={document._user} />, navigationEl);
}

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

document.getElementById("reveal-search").addEventListener("click", (event) => {
  event.stopPropagation();
  event.currentTarget.classList.add("hidden");
  const formEl = event.currentTarget.nextElementSibling;
  formEl.classList.add("flex");
  formEl.classList.remove("hidden");
  formEl.parentNode.classList.add("flex-grow");
  event.currentTarget.parentNode.nextElementSibling.remove();
});

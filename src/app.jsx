import { h, render } from "preact";

import { Navigation } from "./navigation";
import { FollowCase, FollowAddress } from "./follow";
import { NewPasswordForm } from "./forms/new-password";
import { openModal } from "./modals";
import { mapkit, buildEntityMap } from "./maps";

mapkit.init({
  authorizationCallback: (done) => {
    fetch("/mapkit-token")
      .then((res) => res.text())
      .then((token) => done(token))
      .catch((error) => {
        console.error(error);
      });
  },
});

const passwordRecoveryEl = document.getElementById("password-recovery");
if (passwordRecoveryEl) {
  const [el, closeModal] = openModal();
  render(<NewPasswordForm token={passwordRecoveryEl.dataset.token} />, el);
}

const navigationEl = document.getElementById("navigation");
if (navigationEl) {
  render(<Navigation />, navigationEl);
}

mapkit.addEventListener("configuration-change", function (event) {
  switch (event.status) {
    case "Initialized":
      [...document.querySelectorAll(".entity-map")].forEach((el) => {
        const map = new mapkit.Map(el);
        buildEntityMap(map, el.dataset.kennitala);
      });
      break;
    case "Refreshed":
      break;
  }
});

[...document.querySelectorAll(".follow-case")].forEach((button) => {
  const defaultLabel = button.innerText;
  button.innerHTML = "";
  render(
    <FollowCase
      id={button.dataset.id}
      state={button.dataset.state}
      defaultLabel={defaultLabel}
    />,
    button
  );
});

[...document.querySelectorAll(".follow-address")].forEach((button) => {
  render(
    <FollowAddress
      hnitnum={button.dataset.hnitnum}
      state={button.dataset.state}
    />,
    button
  );
});

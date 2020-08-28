import { h, render } from "preact";

import { Navigation } from "./navigation.jsx";
import { Subscriptions } from "./subscriptions.jsx";
import { FollowCase, FollowAddress } from "./follow.jsx";
import { NewPasswordForm } from "./forms/new-password.jsx";
import { openModal } from "./modals.js";
import { mapkit, getEntityMapOptions } from "./maps.jsx";

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

const subscriptionsEl = document.getElementById("subscriptions");
if (subscriptionsEl) {
  render(<Subscriptions />, subscriptionsEl);
}

mapkit.addEventListener("configuration-change", function (event) {
  if (event.status === "Initialized") {
    [...document.querySelectorAll(".entity-map")].forEach(async (el) => {
      const options = await getEntityMapOptions(el.dataset.kennitala);
      if (options) new mapkit.Map(el, options);
    });
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

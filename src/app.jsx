import { h, render } from "preact";

import { Navigation } from "./navigation.jsx";
import { Subscriptions } from "./subscriptions.jsx";
import { Login } from "./accounts.jsx";
import { FollowCase, FollowAddress, FollowEntity } from "./follow.jsx";
import { NewPasswordForm } from "./forms/new-password.jsx";
import { openModal } from "./modals.js";
import { mapkit, getEntityMapOptions, getNearbyMapOptions } from "./maps.jsx";

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

const loginEl = document.getElementById("login");
if (loginEl) {
  const [el, closeModal] = openModal();
  const onSuccess = () => {
    window.location.pathname = loginEl.dataset.redirectTo || "/";
  };
  render(<Login onSuccess={onSuccess} />, el);
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
    [...document.querySelectorAll(".nearby-map")].forEach(async (el) => {
      const options = await getNearbyMapOptions(el.dataset);
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
    <FollowAddress id={button.dataset.id} state={button.dataset.state} />,
    button
  );
});

[...document.querySelectorAll(".follow-entity")].forEach((button) => {
  render(
    <FollowEntity id={button.dataset.kennitala} state={button.dataset.state} />,
    button
  );
});

[...document.querySelectorAll(".tabs")].forEach((tabsEl) => {
  const pageEls = tabsEl.parentElement.querySelectorAll(".tabPage");
  const tabEls = tabsEl.querySelectorAll("button");
  [...tabEls].forEach((tabEl) => {
    const targetPageEl = document.getElementById(tabEl.dataset.target);
    tabEl.addEventListener("click", (event) => {
      pageEls.forEach((pageEl) => {
        pageEl.classList.add("hidden");
      });
      tabEls.forEach((el) => {
        el.classList.remove("selected");
      });
      tabEl.classList.add("selected");
      targetPageEl.classList.remove("hidden");
    });
  });
});

import { h, render } from "preact";

import { Navigation } from "./navigation.jsx";
import { Subscriptions } from "./subscriptions.jsx";
import { Login } from "./accounts.jsx";
import { FollowCase, FollowAddress, FollowEntity } from "./follow.jsx";
import { NewPasswordForm } from "./forms/new-password.jsx";
import { PermitForm } from "./forms/permits.jsx";
import { openModal } from "./modals.js";
import { Unsubscribe } from "./unsubscribe.jsx";
import { PDFViewer } from "./pdfViewer.jsx";
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
  const [modalRender, closeModal] = openModal();
  modalRender(<NewPasswordForm token={passwordRecoveryEl.dataset.token} />);
}

const unsubscribeEl = document.getElementById("unsubscribe");
if (unsubscribeEl) {
  render(<Unsubscribe />, unsubscribeEl);
}

const loginEl = document.getElementById("login");
if (loginEl) {
  const [modalRender, closeModal] = openModal();
  const onSuccess = () => {
    window.location.pathname = loginEl.dataset.redirectTo || "/";
  };
  modalRender(<Login onSuccess={onSuccess} />);
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

[...document.querySelectorAll(".pdf-viewer")].forEach((el) => {
  const innerEl = el.querySelector(".inner");
  const title = el.dataset.title;
  function unmount() {
    render(null, innerEl);
  }
  function mount(index) {
    render(
      <PDFViewer
        pages={pages}
        title={title}
        initialIndex={index}
        onClose={() => {
          unmount();
        }}
      />,
      innerEl
    );
  }
  const pages = [...el.querySelectorAll("a")].map((el, i) => {
    el.addEventListener("click", (event) => {
      event.preventDefault();
      mount(i);
    });
    return el.href;
  });
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

[...document.querySelectorAll(".permit-form")].forEach((formEl) => {
  render(<PermitForm minuteId={formEl.dataset.minuteId} />, formEl);
});

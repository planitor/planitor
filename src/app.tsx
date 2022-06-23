import * as ReactDOM from "react-dom/client";
import { Navigation } from "./navigation";
import { Subscriptions } from "./subscriptions";
import { Login } from "./accounts";
import { FollowCase, FollowAddress, FollowEntity } from "./follow";
import { NewPasswordForm } from "./forms/new-password";
import { PermitForm } from "./forms/permits";
import { openModal } from "./modals";
import { Unsubscribe } from "./unsubscribe";
import { PDFViewer } from "./pdfViewer";
import { mapkit, getEntityMapOptions, getNearbyMapOptions } from "./maps";
import "lazysizes";

import * as Sentry from "@sentry/browser";

if (process.env.SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
  });
  if ("_user" in document) {
    // @ts-expect-error
    const { email, id } = document._user;
    Sentry.setUser({ email, id });
  }
}

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
  ReactDOM.createRoot(unsubscribeEl).render(<Unsubscribe />);
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
  ReactDOM.createRoot(navigationEl).render(<Navigation />);
}

const subscriptionsEl = document.getElementById("subscriptions");
if (subscriptionsEl) {
  ReactDOM.createRoot(subscriptionsEl).render(<Subscriptions />);
}

mapkit.addEventListener("configuration-change", function (event) {
  if (event.status === "Initialized") {
    [...document.querySelectorAll<HTMLElement>(".entity-map")].forEach(
      async (el) => {
        const options = await getEntityMapOptions(el.dataset.kennitala);
        if (options) new mapkit.Map(el, options);
      }
    );
    [...document.querySelectorAll<HTMLElement>(".nearby-map")].forEach(
      async (el) => {
        const options = await getNearbyMapOptions(
          el.dataset as { hnitnum: string; radius: string; days: string }
        );
        if (options) new mapkit.Map(el, options);
      }
    );
  }
});

[...document.querySelectorAll<HTMLElement>(".follow-case")].forEach(
  (button) => {
    const defaultLabel = button.innerText;
    button.innerHTML = "";
    ReactDOM.createRoot(button).render(
      <FollowCase
        id={button.dataset.id}
        state={button.dataset.state}
        defaultLabel={defaultLabel}
      />
    );
  }
);

[...document.querySelectorAll<HTMLElement>(".follow-address")].forEach(
  (button) => {
    ReactDOM.createRoot(button).render(
      <FollowAddress id={button.dataset.id} state={button.dataset.state} />
    );
  }
);

[...document.querySelectorAll<HTMLElement>(".follow-entity")].forEach(
  (button) => {
    ReactDOM.createRoot(button).render(
      <FollowEntity
        id={button.dataset.kennitala}
        state={button.dataset.state}
      />
    );
  }
);

[...document.querySelectorAll<HTMLElement>(".pdf-viewer")].forEach((el) => {
  const innerEl = el.querySelector(".inner");
  const title = el.dataset.title;
  const root = ReactDOM.createRoot(innerEl);
  function render(index: number) {
    root.render(
      <PDFViewer
        pages={pages}
        title={title}
        initialIndex={index}
        onClose={() => root.unmount()}
      />
    );
  }
  const pages = [...el.querySelectorAll("a")].map((el, i) => {
    el.addEventListener("click", (event) => {
      event.preventDefault();
      render(i);
    });
    return el.href;
  });
});

[...document.querySelectorAll<HTMLElement>(".tabs")].forEach((tabsEl) => {
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

[...document.querySelectorAll<HTMLElement>(".permit-form")].forEach(
  (formEl) => {
    ReactDOM.createRoot(formEl).render(
      <PermitForm minuteId={formEl.dataset.minuteId} />
    );
  }
);

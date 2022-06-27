import "lazysizes";
import * as ReactDOM from "react-dom/client";
import { Login } from "./accounts";
import { FollowAddress, FollowCase, FollowEntity } from "./follow";
import { NewPasswordForm } from "./forms/new-password";
import { PermitForm } from "./forms/permits";
import { getEntityMapOptions, getNearbyMapOptions, mapkit } from "./maps";
import { openModal } from "./modals";
import { Navigation } from "./navigation";
import { PDFViewer } from "./pdfViewer";
import { Subscriptions } from "./subscriptions";
import { Unsubscribe } from "./unsubscribe";

import * as Sentry from "@sentry/browser";
import { QueryClientProvider } from "react-query";
import { queryClient } from "./query";

if (process.env.SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
  });
  if ("_user" in document) {
    // @ts-expect-error
    const { email, id } = document._user || {};
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

function render(el: HTMLElement, children: () => React.ReactNode) {
  if (el) {
    ReactDOM.createRoot(el).render(
      <QueryClientProvider client={queryClient}>
        {children()}
      </QueryClientProvider>
    );
  }
}

const passwordRecoveryEl = document.getElementById("password-recovery");
if (passwordRecoveryEl) {
  const [modalRender, closeModal] = openModal();
  modalRender(<NewPasswordForm token={passwordRecoveryEl.dataset.token} />);
}

const loginEl = document.getElementById("login");
if (loginEl) {
  const [modalRender, closeModal] = openModal();
  const onSuccess = () => {
    window.location.pathname = loginEl.dataset.redirectTo || "/";
  };
  modalRender(<Login onSuccess={onSuccess} />);
}

render(document.getElementById("subscriptions"), () => <Subscriptions />);
render(document.getElementById("navigation"), () => <Navigation />);
render(document.getElementById("password-recovery"), () => <Unsubscribe />);

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
    render(button, () => (
      <FollowCase
        id={button.dataset.id}
        state={button.dataset.state}
        defaultLabel={defaultLabel}
      />
    ));
  }
);

[...document.querySelectorAll<HTMLElement>(".follow-address")].forEach(
  (button) => {
    render(button, () => (
      <FollowAddress id={button.dataset.id} state={button.dataset.state} />
    ));
  }
);

[...document.querySelectorAll<HTMLElement>(".follow-entity")].forEach(
  (button) => {
    render(button, () => (
      <FollowEntity
        id={button.dataset.kennitala}
        state={button.dataset.state}
      />
    ));
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
    render(formEl, () => <PermitForm minuteId={formEl.dataset.minuteId} />);
  }
);

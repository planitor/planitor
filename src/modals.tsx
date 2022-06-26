import * as ReactDOM from "react-dom/client";
import { QueryClientProvider } from "react-query";
import { queryClient } from "./query";

const modalEl = document.getElementById("modal");
const classNames = modalEl.classList;
const innerEl = modalEl.querySelector(".form");
const root = ReactDOM.createRoot(innerEl);

export const openModal = (): [
  (component: React.ReactNode) => void,
  () => void
] => {
  /*

  Handle opening and closing the modal window, return the el where React can inject a login form or
  whatever.

   */

  classNames.remove("hidden");
  classNames.add("flex");

  function onOutsideClick(event: MouseEvent) {
    // `Element.closest` traverses parents to find matching selector
    // if we did not find #modal in ancestors we must have clicked somewhere outside
    const clickedOutsideModalEl =
      event.target instanceof Element && !event.target.closest("#modal .inner");
    if (clickedOutsideModalEl && !classNames.contains("hidden")) close();
  }

  const close = () => {
    classNames.add("hidden");
    classNames.remove("flex");
    window.removeEventListener("click", onOutsideClick);
    // root.unmount();
  };

  window.addEventListener("click", onOutsideClick);

  modalEl.querySelectorAll(".close").forEach((el) => {
    el.addEventListener("click", (event) => {
      close();
    });
  });

  const modalRender = (component: React.ReactNode) => {
    root.render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  return [modalRender, close];
};

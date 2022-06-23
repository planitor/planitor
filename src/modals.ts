import * as ReactDOM from "react-dom/client";

export const openModal = () => {
  /*

  Handle opening and closing the modal window, return the el where React can inject a login form or
  whatever.

   */

  const modalEl = document.getElementById("modal");
  const innerEl = modalEl.querySelector(".form");

  const root = ReactDOM.createRoot(innerEl);

  modalEl.classList.remove("hidden");
  const cleanup = () => {
    modalEl.classList.add("hidden");
    innerEl.innerHTML = "<div></div>";
  };
  window.addEventListener("click", (event) => {
    // `Element.closest` traverses parents to find matching selector
    // if we did not find #modal in ancestors we must have clicked somewhere outside
    const clickedOutsideModalEl = !event.target.closest("#modal .inner");
    if (clickedOutsideModalEl) cleanup();
  });

  modalEl.querySelectorAll(".close").forEach((el) => {
    el.addEventListener("click", (event) => {
      cleanup();
    });
  });
  const modalRender = (component) => {
    root.render(component);
  };

  return [modalRender, cleanup];
};

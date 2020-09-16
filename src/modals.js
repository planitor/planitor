import { render, h } from "preact";

export const openModal = () => {
  /* Handle opening and closing the modal window, return the el where Preact
  can inject a login form or whatever.

   */

  const modalEl = document.getElementById("modal");
  const innerEl = modalEl.querySelector(".form");

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

  // if we render multiple times, Preact wants us to use a reference
  // to the same element, returned from `render`
  const modalRender = (component) => {
    render(component, innerEl, innerEl.firstChild);
  };

  return [modalRender, cleanup]; // the section that can be taken over by Preact
};

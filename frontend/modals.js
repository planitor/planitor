export const openModal = () => {
  /* Handle opening and closing the modal window, return the el where Preact
  can inject a login form or whatever.

   */

  const modalEl = document.getElementById("modal");
  modalEl.classList.remove("hidden");
  const close = () => {
    modalEl.classList.add("hidden");
  };
  window.addEventListener("click", (event) => {
    // `Element.closest` traverses parents to find matching selector
    // if we did not find #modal in ancestors we must have clicked somewhere outside
    const clickedOutsideModalEl = !event.target.closest("#modal .inner");
    if (clickedOutsideModalEl) close();
  });

  modalEl.querySelectorAll(".close").forEach((el) => {
    el.addEventListener("click", (event) => {
      close();
    });
  });

  return modalEl.querySelector(".form"); // the section that can be taken over by Preact
};

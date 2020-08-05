import { h, render } from "preact";

import "./maps";
import { Navigation } from "./navigation";
import { FollowCase, FollowAddress } from "./follow";

const navigationEl = document.getElementById("navigation");
if (navigationEl) {
  render(<Navigation />, navigationEl);
}

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

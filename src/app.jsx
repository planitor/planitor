import { h, render } from "preact";

import "./maps";
import { Navigation } from "./navigation";
import { FollowCase } from "./follow";

const navigationEl = document.getElementById("navigation");
if (navigationEl) {
  render(<Navigation />, navigationEl);
}

[...document.querySelectorAll(".follow")].forEach((button) => {
  render(
    <FollowCase id={button.dataset.id} state={button.dataset.state} />,
    button
  );
});

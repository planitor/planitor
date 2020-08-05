import { h, render } from "preact";
import { useState } from "preact/hooks";
import classNames from "classnames";

import { api } from "./api";
import { openModal } from "./modals";

export const FollowCase = (props) => {
  const { id, state } = props;
  const [hover, setHover] = useState(false);
  const [following, setFollowing] = useState(state === "following");
  const [form, setForm] = useState({ isLoading: false, error: null });
  const onClick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (form.isLoading) return;
    const toggle = () => {
      setForm({ isLoading: true, error: null });
      (following ? api.unfollowCase(id) : api.followCase(id))
        .then((response) => {
          setFollowing(!following);
          setHover(false);
          setForm({ isLoading: false, error: null });
        })
        .catch(function (error) {
          setForm({ isLoading: false, error: error });
        });
    };
    if (document._user === null) {
      const [el, closeModal] = openModal();
      render(
        <p class="text-center">
          Vaktarinn stendur öllum til boða gegn mánaðargjaldi. Til að fá aðgang
          sendu okkur línu á{" "}
          <a class="text-midnight underline" href="mailto:hallo@planitor.io">
            hallo@planitor.io
          </a>
          .
        </p>,
        el
      );
    } else {
      toggle();
    }
  };

  return (
    <button
      class={classNames("px-4 py-2 border rounded-lg font-bold", {
        "text-gray-500 border-gray-500": form.isLoading,
        "bg-midnight text-white": following && !form.isLoading,
        "text-midnight": !following && !form.isLoading,
        "border-midnight": !form.isLoading,
        error: form.error,
      })}
      onClick={onClick}
      onMouseOver={(event) => {
        setHover(true);
      }}
      onMouseOut={(event) => {
        setHover(false);
      }}
    >
      {(() => {
        if (hover) {
          return following ? "Afvakta" : "Vakta";
        } else {
          return following ? "Vaktað" : "Vakta";
        }
      })()}
    </button>
  );
};

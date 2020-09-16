import { h, render } from "preact";
import { useState } from "preact/hooks";
import classNames from "classnames";

import { api } from "./api";
import { openModal } from "./modals";

const Button = (props) => {
  const { loading, onClick, hover, setHover, following, defaultLabel } = props;
  return (
    <button
      class={classNames("btn sm:inline block mx-auto", {
        "text-gray-500 border-gray-500": loading,
        "bg-midnight text-white": following && !loading,
        "text-midnight": !following && !loading,
        "border-midnight": !loading,
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
          return following ? "Afvakta" : defaultLabel || "Vakta";
        } else {
          return following ? "Vaktað" : defaultLabel || "Vakta";
        }
      })()}
    </button>
  );
};

const Banner = (props) => {
  const Link = () => {
    return (
      <a class="text-midnight underline" href="mailto:hallo@planitor.io">
        hallo@planitor.io
      </a>
    );
  };
  return (
    <p class="text-center">
      Vaktarinn stendur öllum til boða gegn mánaðargjaldi. <br />
      Til að fá aðgang sendu okkur línu á <Link />.
    </p>
  );
};

const Follow = (props) => {
  const { id, state, defaultLabel, unfollowApi, followApi } = props;
  const [hover, setHover] = useState(false);
  const [following, setFollowing] = useState(state === "following");
  const [form, setForm] = useState({ isLoading: false, error: null });
  const onClick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (form.isLoading) return;
    const toggle = () => {
      setForm({ isLoading: true, error: null });
      (following ? unfollowApi(id) : followApi(id))
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
      const [modalRender, _] = openModal();
      modalRender(<Banner />);
    } else {
      toggle();
    }
  };
  return (
    <Button
      loading={form.isLoading}
      following={following}
      hover={hover}
      setHover={setHover}
      onClick={onClick}
      defaultLabel={defaultLabel || null}
    />
  );
};

export const FollowCase = (props) => {
  return (
    <Follow
      unfollowApi={api.unfollowCase}
      followApi={api.followCase}
      {...props}
    />
  );
};

export const FollowAddress = (props) => {
  return (
    <Follow
      unfollowApi={api.unfollowAddress}
      followApi={api.followAddress}
      {...props}
    />
  );
};

export const FollowEntity = (props) => {
  return (
    <Follow
      unfollowApi={api.unfollowEntity}
      followApi={api.followEntity}
      {...props}
    />
  );
};

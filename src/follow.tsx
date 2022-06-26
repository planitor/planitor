import classNames from "classnames";
import { useState } from "react";

import {
  useFollowAddress,
  useFollowCase,
  useFollowEntity,
  useUnfollowAddress,
  useUnfollowCase,
  useUnfollowEntity,
} from "./api/types";
import { FollowButton } from "./forms/widgets";
import { openModal } from "./modals";

const Banner = () => {
  const Link = () => {
    return (
      <a
        className="text-planitor-blue underline"
        href="mailto:hallo@planitor.io"
      >
        hallo@planitor.io
      </a>
    );
  };
  return (
    <p className="text-center">
      Vaktarinn stendur öllum til boða gegn mánaðargjaldi. <br />
      Til að fá aðgang sendu okkur línu á <Link />.
    </p>
  );
};

const Follow = ({
  state,
  defaultLabel,
  unfollow,
  follow,
}: {
  state?: "following";
  defaultLabel?: string;
  follow: () => Promise<void>;
  unfollow: () => Promise<void>;
}) => {
  const [hover, setHover] = useState(false);
  const [following, setFollowing] = useState(state === "following");
  const [form, setForm] = useState({ isLoading: false, error: null });
  const onClick = () => {
    if (form.isLoading) return;
    const toggle = () => {
      setForm({ isLoading: true, error: null });
      (following ? unfollow() : follow())
        .then(() => {
          setFollowing(!following);
          setHover(false);
          setForm({ isLoading: false, error: null });
        })
        .catch(function (error) {
          setForm({ isLoading: false, error: error });
        });
    };
    // @ts-expect-error
    if (document._user === null) {
      const [modalRender, _] = openModal();
      modalRender(<Banner />);
    } else {
      toggle();
    }
  };
  return (
    <FollowButton
      loading={form.isLoading}
      following={following}
      hover={hover}
      setHover={setHover}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        onClick();
      }}
      defaultLabel={defaultLabel}
    />
  );
};

export const FollowCase = ({
  id,
  ...props
}: {
  id: string;
  state?: "following";
  defaultLabel?: string;
}) => {
  const { mutateAsync: unfollow } = useUnfollowCase();
  const { mutateAsync: follow } = useFollowCase();
  return (
    <Follow
      unfollow={async () => {
        await unfollow({ caseId: Number(id) });
      }}
      follow={async () => {
        await follow({ caseId: Number(id) });
      }}
      {...props}
    />
  );
};
export const FollowAddress = ({
  id,
  ...props
}: {
  id: string;
  state?: "following";
  defaultLabel?: string;
}) => {
  const { mutateAsync: unfollow } = useUnfollowAddress();
  const { mutateAsync: follow } = useFollowAddress();
  return (
    <Follow
      unfollow={async () => {
        await unfollow({ hnitnum: Number(id) });
      }}
      follow={async () => {
        await follow({ hnitnum: Number(id) });
      }}
      {...props}
    />
  );
};
export const FollowEntity = ({
  id,
  ...props
}: {
  id: string;
  state?: "following";
  defaultLabel?: string;
}) => {
  const { mutateAsync: unfollow } = useUnfollowEntity();
  const { mutateAsync: follow } = useFollowEntity();
  return (
    <Follow
      unfollow={async () => {
        await unfollow({ kennitala: id });
      }}
      follow={async () => {
        await follow({ kennitala: id });
      }}
      {...props}
    />
  );
};

import { h, render } from "preact";
import { useState, useRef, useEffect } from "preact/hooks";
import classNames from "classnames";
import { Login } from "./accounts";
import { openModal } from "./modals";
import { api } from "./api";
import { PersonFill, MagnifyingGlass } from "./symbols";

const LogoutButton = (props) => {
  const onClick = (event) => {
    event.stopPropagation();
    event.preventDefault();
    api.logout().then((response) => {
      localStorage.removeItem("token");
      location.reload();
    });
  };
  return (
    <a
      onClick={onClick}
      href="/notendur/logout"
      role="button"
      class="text-sm font-bold text-powder-light"
    >
      Útskrá
    </a>
  );
};

const LoginButton = (props) => {
  const { onLogin } = props;
  const onClick = (event) => {
    event.stopPropagation();
    event.preventDefault();
    const [el, closeModal] = openModal();
    const onSuccess = () => {
      onLogin();
      closeModal();
    };
    render(<Login onSuccess={onSuccess} />, el);
  };

  return (
    <a href="#" role="button" onClick={onClick} class="block p-2">
      <PersonFill />
    </a>
  );
};

const User = (props) => {
  const [user, setUser] = useState(document._user);
  const onLogin = () => {
    api
      .getMe()
      .then((response) => {
        setUser(response.data);
        document._user = response.data;
      })
      .catch(function (error) {
        console.log(error);
      });
  };
  if (!!user) {
    return (
      <div class="flex flex-row sm:flex-col">
        <div>
          <a href="/notendur/stillingar" class="text-sm block truncate">
            <span
              class="sm:hidden inline-block pl-4"
              style="position: relative; top: 2px;"
            >
              <PersonFill />
            </span>
            <span class="hidden sm:inline">{user.email}</span>
          </a>
        </div>
        <div class="order-first sm:order-last flex-grow">
          <LogoutButton />
        </div>
      </div>
    );
  }
  return <LoginButton onLogin={onLogin} />;
};

export const Navigation = () => {
  const [isSearchExpanded, setIsSearchExpanded] = useState(
    typeof document._searchQuery === "string"
  );
  const [value, setValue] = useState(document._searchQuery);

  const onChange = (event) => {
    setValue(event.target.value);
  };

  // When mobile user clicks to expand search, focus the input
  const input = useRef(null);
  useEffect(() => {
    input.current && input.current.value && input.current.focus();
  }, [isSearchExpanded]);

  return (
    <div class="flex justify-between items-center align-middle h-12">
      <div
        class={classNames(
          "sm:order-2 sm:flex-grow text-center sm:px-10 sm:max-w-4xl",
          {
            "flex-grow": isSearchExpanded,
          }
        )}
      >
        {!isSearchExpanded && (
          <span
            onClick={() => {
              setIsSearchExpanded(true);
            }}
            role="button"
            class="sm:hidden block"
          >
            <MagnifyingGlass />
          </span>
        )}
        <div
          class={classNames("sm:flex pr-4 sm:pr-0", {
            hidden: !isSearchExpanded,
          })}
        >
          <form
            class="search flex bg-white bg-opacity-25 rounded-md items-center mr-3 px-3 w-full"
            method="GET"
            action="/leit"
          >
            <MagnifyingGlass />
            <input
              value={value}
              ref={input}
              onChange={onChange}
              name="q"
              size="1"
              class="bg-transparent flex-grow py-2 px-2 text-sm font-thin overflow-hidden focus:outline-none"
              placeholder="Leit - t.d. 'Reitir ehf.', 'Brautarholt' eða 'gistiheimili'"
            />
          </form>
        </div>
      </div>
      <div
        class={classNames("flex-grow sm:order-1 sm:flex-grow-0 text-center", {
          hidden: isSearchExpanded,
          "sm:block": isSearchExpanded,
        })}
      >
        <a href="/s" class="font-black text-lg sm:text-xl">
          Planitor
        </a>
      </div>
      <div class="order-last text-right">
        <User />
      </div>
    </div>
  );
};

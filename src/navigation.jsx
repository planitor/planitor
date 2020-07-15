import { h } from "preact";
import { useState } from "preact/hooks";
import classNames from "classnames";

const MagnifyingGlass = (props) => {
  return (
    <svg
      class="inline h-5 w-5"
      width="112px"
      height="112px"
      viewBox="0 0 112 112"
    >
      <g transform="translate(-622.000000, -48.000000)" fill-rule="nonzero">
        <path d="M726.662109,159.421875 C730.470703,159.421875 733.166016,156.492188 733.166016,152.742188 C733.166016,150.984375 732.580078,149.34375 731.291016,148.054688 L703.693359,120.398438 C709.494141,112.78125 712.951172,103.347656 712.951172,93.09375 C712.951172,68.3085938 692.677734,48.0351562 667.892578,48.0351562 C643.107422,48.0351562 622.833984,68.3085938 622.833984,93.09375 C622.833984,117.878906 643.107422,138.152344 667.892578,138.152344 C677.677734,138.152344 686.701172,134.988281 694.083984,129.714844 L721.857422,157.488281 C723.146484,158.777344 724.845703,159.421875 726.662109,159.421875 Z M667.892578,128.425781 C648.556641,128.425781 632.560547,112.429688 632.560547,93.09375 C632.560547,73.7578125 648.556641,57.7617188 667.892578,57.7617188 C687.228516,57.7617188 703.224609,73.7578125 703.224609,93.09375 C703.224609,112.429688 687.228516,128.425781 667.892578,128.425781 Z"></path>
      </g>
    </svg>
  );
};

const PersonFill = (props) => {
  return (
    <svg
      width="112px"
      height="112px"
      class="inline h-5 w-5"
      viewBox="0 0 112 112"
    >
      <g transform="translate(-628.000000, -53.000000)" fill-rule="nonzero">
        <path d="M677.529297,104.109375 C690.068359,104.109375 700.966797,92.859375 700.966797,78.2109375 C700.966797,63.7382812 690.068359,53.015625 677.529297,53.015625 C664.990234,53.015625 654.091797,63.9726562 654.091797,78.328125 C654.091797,92.859375 664.931641,104.109375 677.529297,104.109375 Z M714.267578,158.367188 C723.525391,158.367188 726.806641,155.730469 726.806641,150.574219 C726.806641,135.457031 707.880859,114.597656 677.470703,114.597656 C647.119141,114.597656 628.193359,135.457031 628.193359,150.574219 C628.193359,155.730469 631.474609,158.367188 640.673828,158.367188 L714.267578,158.367188 Z"></path>
      </g>
    </svg>
  );
};

const User = (props) => {
  const { user } = props;
  if (!!user) {
    return (
      <div class="flex flex-row sm:flex-col">
        <div>
          <a href="/" class="text-sm block truncate">
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
          <a
            href="/notendur/logout"
            id="logout-button"
            class="text-sm font-bold text-powder-light"
          >
            Útskrá
          </a>
        </div>
      </div>
    );
  }
  return (
    <div id="login-button" role="button">
      <PersonFill />
    </div>
  );
};

export const Navigation = (props) => {
  const { user } = props;
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const searchExpand = () => {
    setIsSearchExpanded(true);
  };
  return (
    <div class="flex items-center p-2 sm:px-6 h-16">
      <div
        class={classNames("sm:order-2 sm:flex-grow text-center sm:px-10", {
          "flex-grow": isSearchExpanded,
        })}
      >
        {!isSearchExpanded && (
          <a onClick={searchExpand} role="button" class="sm:hidden block">
            <MagnifyingGlass />
          </a>
        )}
        <form
          class={classNames(
            "search sm:flex bg-white bg-opacity-25 rounded-md items-center mr-3 px-3 md:mx-12",
            { hidden: !isSearchExpanded, flex: isSearchExpanded }
          )}
          method="GET"
          action="/leit"
        >
          <MagnifyingGlass />
          <input
            value=""
            name="q"
            size="1"
            class="bg-transparent flex-grow py-2 px-2 text-sm font-thin overflow-hidden"
            placeholder="Leit - t.d. 'Reitir ehf.', 'Brautarholt' eða 'gistiheimili'"
          />
        </form>
      </div>

      {!isSearchExpanded && (
        <div class="flex-grow sm:order-1 sm:flex-grow-0 text-center">
          <a href="/s" class="font-black text-lg sm:text-xl">
            Planitor
          </a>
        </div>
      )}

      <div class="order-last text-right">
        <User user={user} />
      </div>
    </div>
  );
};

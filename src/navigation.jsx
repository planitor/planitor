import { h, render } from "preact";
import { useState, useRef, useEffect } from "preact/hooks";
import classNames from "classnames";
import { Login } from "./accounts.jsx";
import { openModal } from "./modals";
import { api } from "./api";
import { PersonFill, MagnifyingGlass } from "./symbols.jsx";

const LogoutButton = (props) => {
  const onClick = (event) => {
    event.stopPropagation();
    event.preventDefault();
    api.logout().then((response) => {
      localStorage.removeItem("token");
      window.location.pathname = "/";
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
    const [modalRender, closeModal] = openModal();
    const onSuccess = () => {
      onLogin();
      closeModal();
    };
    modalRender(<Login onSuccess={onSuccess} />);
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

  const onSubmit = (event) => {
    event.stopPropagation();
    event.preventDefault();
    if (window.fathom !== undefined) {
      window.fathom.trackGoal("PBZT1SCW", 0);
    }
    event.target.submit();
  };

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
            onSubmit={onSubmit}
          >
            <MagnifyingGlass />
            <input
              value={value}
              ref={input}
              onChange={onChange}
              name="q"
              size="1"
              class="bg-transparent flex-grow py-2 px-2 text-sm font-light overflow-hidden focus:outline-none"
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
        <a href="/s" alt="Planitor Logo" class="text-white">
          <svg viewBox="0 0 141 175" class="h-6 inline sm:hidden">
            <g stroke="none" stroke-width="1" fill-rule="evenodd">
              <g transform="translate(-1302.000000, -561.000000)">
                <g transform="translate(1302.000000, 561.000000)">
                  <path d="M42.6751907,24.758 C42.8521907,46.802 43.1141907,69.166 43.1141907,69.166 C43.1191907,103.766 43.1151907,138.365 43.1151907,172.963 C43.1151907,173.589 43.1151907,174.215 43.1151907,174.971 C29.0461907,174.971 15.0921907,174.971 0.939190743,174.971 C0.911190743,174.262 0.856190743,173.52 0.856190743,172.778 C0.851190743,143.981 0.235190743,115.254 0.218190743,86.456 C0.213190743,78.106 -0.563809257,64.484 0.845190743,56.488 C2.74619074,45.704 6.64619074,40.115 8.90019074,36.427 C18.7071907,20.378 48.2991907,0.641 48.2991907,0.641 C48.2991907,0.641 42.5331907,7.075 42.6751907,24.758"></path>
                  <path d="M140.798191,0 C140.798191,17.598 140.800191,34.049 140.800191,51.665 L47.9661907,51.665 C47.9651907,40.874 47.9461907,30.261 47.9661907,19.225 C47.9811907,10.528 50.6631907,0 64.3291907,0 C65.5401907,0 140.798191,0 140.798191,0"></path>
                  <path d="M94.9451907,65.215 C91.9521907,70.768 90.7271907,79.317 90.4051907,86.243 C90.1321907,92.094 90.3021907,97.982 90.3481907,103.852 C90.4021907,110.643 90.6011907,117.432 90.6191907,124.222 C90.6611907,140.288 90.6331907,156.354 90.6331907,172.419 C90.6331907,173.195 90.6331907,173.971 90.6331907,174.924 C76.5591907,174.924 62.5521907,174.924 48.2281907,174.924 C48.2281907,173.121 48.2281907,171.239 48.2281907,169.357 C48.2281907,159.803 48.3351907,150.247 48.1981907,140.697 C47.9571907,105.403 57.0381907,91.49 65.9201907,82.998 C77.1421907,72.269 94.9451907,65.215 94.9451907,65.215"></path>
                  <path d="M140.839191,59.58 L140.839191,95.85 C140.839191,104.462 133.858191,111.443 125.246191,111.443 L95.7421907,111.443 L95.7411907,111.442 C95.7491907,103.113 95.7051907,94.784 95.7541907,86.454 C95.7881907,80.657 96.4771907,75.047 99.3201907,70.201 C103.460191,63.143 109.231191,59.732 116.040191,59.453 C124.119191,59.122 132.214191,59.359 140.302191,59.36 C140.459191,59.36 140.615191,59.485 140.839191,59.58"></path>
                </g>
              </g>
            </g>
          </svg>
          <svg viewBox="0 0 843 176" class="h-6 hidden sm:inline">
            <g stroke="none" stroke-width="1" fill-rule="evenodd">
              <g transform="translate(-123.000000, -101.000000)">
                <g transform="translate(123.000000, 101.000000)" fill="#FFFFFF">
                  <g transform="translate(215.285191, 17.394101)">
                    <path d="M17.101,89.8134819 L68.301,89.8 C76.301,89.8 82.951,88.384 88.25,85.55 C93.551,82.717 97.516,78.767 100.151,73.7 C102.784,68.634 104.101,62.735 104.101,56 C104.101,49.201 102.833,43.4 100.301,38.6 C97.766,33.8 93.867,30.134 88.601,27.6 C83.333,25.068 76.567,23.8 68.301,23.8 C45.5481646,23.8 28.4835381,23.8 17.1071204,23.8 L17.101,23.8 L17.101,89.8134819 Z M1.42108547e-14,156.3 L1.42108547e-14,8.8 L70.401,8.8 C81.801,8.8 91.266,10.917 98.801,15.15 C106.333,19.384 111.966,25.068 115.701,32.2 C119.434,39.334 121.301,47.267 121.301,56 C121.301,64.735 119.383,72.8 115.551,80.2 C111.716,87.6 106.016,93.55 98.451,98.05 C90.883,102.55 81.534,104.8 70.401,104.8 L17.101,104.8 L17.101,156.3 L1.42108547e-14,156.3 Z"></path>
                    <polygon points="127.7 156.3 144.499 156.3 144.499 0 127.7 0"></polygon>
                    <path d="M195.398,143 C202.264,143 208.464,141.95 213.998,139.85 C219.531,137.75 223.931,134.634 227.199,130.5 C230.464,126.367 232.098,121.235 232.098,115.1 L232.117641,101.710536 C228.610499,102.789856 224.554033,103.702632 219.949,104.45 C213.581,105.485 206.931,106.334 199.998,107 C189.931,107.935 182.348,109.7 177.248,112.3 C172.148,114.9 169.598,119.267 169.598,125.4 C169.598,131.2 171.699,135.584 175.898,138.55 C180.098,141.517 186.598,143 195.398,143 Z M171.548,154.5 C165.514,151.967 160.831,148.318 157.498,143.55 C154.163,138.784 152.498,133.068 152.498,126.4 C152.498,119.467 154.298,113.685 157.898,109.05 C161.498,104.417 166.564,100.8 173.098,98.2 C179.631,95.6 187.231,93.867 195.898,93 C208.964,91.667 218.264,90.35 223.798,89.05 C229.331,87.75 232.098,85.634 232.098,82.7 C232.098,82.634 232.098,82.584 232.098,82.55 C232.098,82.517 232.098,82.467 232.098,82.4 C232.098,76.267 229.598,71.685 224.598,68.65 C219.598,65.617 212.364,64.1 202.898,64.1 C193.031,64.1 185.364,65.818 179.898,69.25 C174.431,72.685 171.699,78.235 171.699,85.9 L154.898,85.9 C154.898,77.967 156.931,71.217 160.998,65.65 C165.064,60.084 170.714,55.834 177.949,52.9 C185.181,49.967 193.531,48.5 202.998,48.5 C211.663,48.5 219.481,49.818 226.449,52.45 C233.413,55.084 238.949,58.985 243.048,64.15 C247.148,69.318 249.199,75.7 249.199,83.3 C249.199,84.7 249.199,86.084 249.199,87.45 C249.199,88.818 249.199,90.2 249.199,91.6 L249.199,136.3 C249.199,138.634 249.298,140.9 249.498,143.1 C249.699,145.3 250.031,147.235 250.498,148.9 C251.098,150.9 251.764,152.517 252.498,153.75 C253.231,154.985 253.831,155.834 254.298,156.3 L237.199,156.3 C236.864,155.967 236.364,155.185 235.699,153.95 C235.031,152.717 234.398,151.267 233.798,149.6 C233.331,148.267 232.964,146.584 232.699,144.55 L232.596027,143.699738 C230.817123,145.850877 228.634355,147.817723 226.048,149.6 C222.081,152.334 217.298,154.467 211.699,156 C206.098,157.533 199.764,158.3 192.699,158.3 C184.631,158.3 177.581,157.033 171.548,154.5 Z"></path>
                    <path d="M333.397,156.3 L333.397,105.4 C333.397,102.334 333.397,99.818 333.397,97.85 C333.397,95.884 333.397,94 333.397,92.2 C333.397,86.667 332.462,81.834 330.597,77.701 C328.73,73.568 325.797,70.367 321.797,68.1 C317.797,65.834 312.563,64.7 306.097,64.7 C300.43,64.7 295.18,66.15 290.347,69.05 C285.513,71.95 281.647,75.85 278.747,80.75 C275.847,85.65 274.397,91.134 274.397,97.2 L274.395437,65.6839366 C277.940683,61.2256829 282.223876,57.5146353 287.247,54.55 C294.079,50.517 301.53,48.5 309.597,48.5 C317.797,48.5 324.962,50.068 331.097,53.2 C337.23,56.334 341.98,60.818 345.347,66.65 C348.712,72.485 350.397,79.5 350.397,87.7 C350.397,90.634 350.397,93.834 350.397,97.3 C350.397,100.767 350.397,104 350.397,107 L350.397,156.3 L333.397,156.3 Z M257.397,156.3 L274.397,156.3 L274.397,50.1 L257.397,50.1 L257.397,156.3 Z"></path>
                    <polygon points="360.996 156.3 377.795 156.3 377.795 50.1 360.996 50.1"></polygon>
                    <path d="M431.495,157.9 C428.228,157.9 425.028,157.533 421.895,156.8 C418.76,156.068 415.945,154.75 413.445,152.85 C410.945,150.95 408.96,148.25 407.495,144.75 C406.028,141.25 405.294,136.735 405.294,131.2 C405.294,129.8 405.294,128.35 405.294,126.85 C405.294,125.35 405.294,123.767 405.294,122.1 L405.294,65.1 L376.395,65.1 L376.395,50.1 L395.995,50.1 C398.26,50.1 400.028,50.017 401.294,49.85 C402.56,49.685 403.478,49.25 404.044,48.55 C404.611,47.85 404.96,46.75 405.095,45.25 C405.228,43.75 405.294,41.667 405.294,39 L405.294,14.9 L422.395,14.9 L422.395,50.1 L455.595,50.1 L455.595,65.1 L422.395,65.1 L422.395,116.6 C422.395,118.068 422.395,119.5 422.395,120.9 C422.395,122.3 422.395,123.6 422.395,124.8 C422.395,130.467 423.078,134.9 424.445,138.1 C425.81,141.3 428.895,142.9 433.695,142.9 C435.627,142.9 437.46,142.735 439.195,142.4 C440.927,142.068 442.228,141.735 443.095,141.4 L443.095,156.2 C441.96,156.6 440.377,156.983 438.345,157.35 C436.31,157.716 434.028,157.9 431.495,157.9"></path>
                    <path d="M504.197,142.6 C511.53,142.6 517.997,140.967 523.597,137.7 C529.197,134.435 533.58,129.834 536.747,123.9 C539.913,117.967 541.497,111.034 541.497,103.1 C541.497,95.167 539.913,88.284 536.747,82.45 C533.58,76.617 529.197,72.117 523.597,68.95 C517.997,65.784 511.53,64.201 504.197,64.201 C496.93,64.201 490.48,65.784 484.847,68.95 C479.212,72.117 474.813,76.617 471.647,82.45 C468.48,88.284 466.897,95.167 466.897,103.1 C466.897,111.034 468.48,117.967 471.647,123.9 C474.813,129.834 479.212,134.435 484.847,137.7 C490.48,140.967 496.93,142.6 504.197,142.6 Z M504.197,158.2 C493.53,158.2 484.113,155.818 475.947,151.05 C467.78,146.284 461.38,139.75 456.747,131.45 C452.113,123.15 449.797,113.7 449.797,103.1 C449.797,92.5 452.113,83.1 456.747,74.9 C461.38,66.7 467.78,60.267 475.947,55.6 C484.113,50.935 493.53,48.6 504.197,48.6 C514.863,48.6 524.28,50.935 532.447,55.6 C540.613,60.267 547.013,66.7 551.647,74.9 C556.28,83.1 558.597,92.5 558.597,103.1 C558.597,113.7 556.28,123.15 551.647,131.45 C547.013,139.75 540.613,146.284 532.447,151.05 C524.28,155.818 514.863,158.2 504.197,158.2 L504.197,158.2 Z"></path>
                    <path d="M565.095,50.1 L582.095,50.1 L582.095,82.7 L582.089028,64.0015464 C583.260364,62.1104587 584.612302,60.3265571 586.145,58.65 C588.978,55.55 592.528,53.084 596.795,51.25 C601.061,49.417 606.061,48.5 611.795,48.5 C616.061,48.5 619.545,48.85 622.246,49.55 C624.946,50.25 626.628,50.8 627.295,51.2 L622.895,67.9 C622.228,67.435 620.878,66.834 618.845,66.1 C616.811,65.367 613.928,65 610.196,65 C604.661,65 600.079,66 596.446,68 C592.811,70 589.946,72.65 587.845,75.95 C585.746,79.25 584.261,82.834 583.395,86.7 C582.528,90.568 582.095,94.4 582.095,98.2 L582.095,156.3 L565.095,156.3 L565.095,50.1 Z"></path>
                    <path d="M379.834,25.338 C379.834,31.104 375.161,35.777 369.395,35.777 C363.63,35.777 358.956,31.104 358.956,25.338 C358.956,19.573 363.63,14.9 369.395,14.9 C375.161,14.9 379.834,19.573 379.834,25.338"></path>
                    <path d="M617.073,147.461 C617.073,153.226 612.399,157.9 606.634,157.9 C600.869,157.9 596.195,153.226 596.195,147.461 C596.195,141.696 600.869,137.022 606.634,137.022 C612.399,137.022 617.073,141.696 617.073,147.461"></path>
                  </g>
                  <g transform="translate(0.000000, 0.723101)">
                    <path d="M42.6751907,24.758 C42.8521907,46.802 43.1141907,69.166 43.1141907,69.166 C43.1191907,103.766 43.1151907,138.365 43.1151907,172.963 C43.1151907,173.589 43.1151907,174.215 43.1151907,174.971 C29.0461907,174.971 15.0921907,174.971 0.939190743,174.971 C0.911190743,174.262 0.856190743,173.52 0.856190743,172.778 C0.851190743,143.981 0.235190743,115.254 0.218190743,86.456 C0.213190743,78.106 -0.563809257,64.484 0.845190743,56.488 C2.74619074,45.704 6.64619074,40.115 8.90019074,36.427 C18.7071907,20.378 48.2991907,0.641 48.2991907,0.641 C48.2991907,0.641 42.5331907,7.075 42.6751907,24.758"></path>
                    <path d="M140.798191,0 C140.798191,17.598 140.800191,34.049 140.800191,51.665 L47.9661907,51.665 C47.9651907,40.874 47.9461907,30.261 47.9661907,19.225 C47.9811907,10.528 50.6631907,0 64.3291907,0 C65.5401907,0 140.798191,0 140.798191,0"></path>
                    <path d="M94.9451907,65.215 C91.9521907,70.768 90.7271907,79.317 90.4051907,86.243 C90.1321907,92.094 90.3021907,97.982 90.3481907,103.852 C90.4021907,110.643 90.6011907,117.432 90.6191907,124.222 C90.6611907,140.288 90.6331907,156.354 90.6331907,172.419 C90.6331907,173.195 90.6331907,173.971 90.6331907,174.924 C76.5591907,174.924 62.5521907,174.924 48.2281907,174.924 C48.2281907,173.121 48.2281907,171.239 48.2281907,169.357 C48.2281907,159.803 48.3351907,150.247 48.1981907,140.697 C47.9571907,105.403 57.0381907,91.49 65.9201907,82.998 C77.1421907,72.269 94.9451907,65.215 94.9451907,65.215"></path>
                    <path d="M140.839191,59.58 L140.839191,95.85 C140.839191,104.462 133.858191,111.443 125.246191,111.443 L95.7421907,111.443 L95.7411907,111.442 C95.7491907,103.113 95.7051907,94.784 95.7541907,86.454 C95.7881907,80.657 96.4771907,75.047 99.3201907,70.201 C103.460191,63.143 109.231191,59.732 116.040191,59.453 C124.119191,59.122 132.214191,59.359 140.302191,59.36 C140.459191,59.36 140.615191,59.485 140.839191,59.58"></path>
                  </g>
                </g>
              </g>
            </g>
          </svg>
        </a>
      </div>
      <div class="order-last text-right">
        <User />
      </div>
    </div>
  );
};

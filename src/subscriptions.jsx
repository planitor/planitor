import { Fragment, h } from "preact";
import { useState, useRef, useEffect } from "preact/hooks";
import { api } from "./api";
import { TrashFill, BadgePlusRadiowavesRight } from "./symbols.jsx";

const SelectWidget = ({ value, onChange, isDisabled, children }) => {
  return (
    <div class="inline-block relative text-sm lg:text-base">
      <select
        value={value}
        onChange={onChange}
        disabled={isDisabled}
        class="block appearance-none w-full border border-gray-400 hover:border-gray-500 px-1 lg:px-4 py-1 lg:py-2 pr-8 mr-3 rounded shadow leading-tight focus:outline-none focus:shadow-outline"
      >
        {children}
      </select>
      <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
        <svg class="fill-current h-4 w-4" viewBox="0 0 20 20">
          <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
        </svg>
      </div>
    </div>
  );
};

const SubscriptionLoading = () => {
  return (
    <div class="rounded-lg shadow-sm p-4 w-full bg-white mb-4">
      <div class="animate-pulse flex flex-row">
        <div class="bg-gray-400 rounded w-3/4 mr-4 h-8"></div>
        <div class="bg-gray-400 rounded w-1/4 mr-4 h-8"></div>
        <div class="bg-gray-400 rounded w-16 h-8"></div>
      </div>
    </div>
  );
};

const Case = ({ serial, id }) => {
  return <a href={`/cases/${id}`}>{serial}</a>;
};

const Search = ({ search_query }) => {
  return <a href={`/leit?q=${search_query}`}>„{search_query}“</a>;
};

const Address = ({ name, hnitnum, radius, onChangeRadius }) => {
  return <a href={`/hnit/${hnitnum}`}>{name}</a>;
};

const Entity = ({ kennitala, name }) => {
  return <a href={`/f/${kennitala}`}>{name}</a>;
};

const Subscription = (props) => {
  const { subscription } = props;

  const [isLoading, setLoading] = useState(false);
  const [isDeleted, setDeleted] = useState(false);
  const [data, setData] = useState(subscription);

  const { id, active, immediate } = data;
  let value = immediate ? "immediate" : "weekly";

  if (!active) {
    value = "never";
  }

  if (isDeleted) return null;

  const onDelete = async (event) => {
    const isConfirmed = confirm(
      "Ertu viss um að þú viljir fjárlægja þennan vaktara?"
    );
    if (!isConfirmed) return;
    setLoading(true);
    const data = await api.deleteSubscription(id).then((response) => {
      return response.data;
    });
    setDeleted(true);
  };

  const onChange = async (event) => {
    const { value } = event.target;
    const requestData = {
      active: value !== "never",
      immediate: value === "immediate",
    };
    setLoading(true);
    const responseData = await api
      .updateSubscription(id, requestData)
      .then((response) => {
        return response.data;
      });
    setLoading(false);
    setData(responseData);
  };

  const onChangeRadius = async (event) => {
    const { value } = event.target;
    const responseData = await api
      .updateSubscription(id, { radius: Number(value) })
      .then((response) => {
        return response.data;
      });
    setLoading(false);
    setData(responseData);
  };

  return (
    <div class="sm:rounded-lg sm:shadow-sm pb-2 sm:p-4 w-full sm:bg-white mb-2 sm:mb-4">
      <div class="flex flex-col md:flex-row align-middle">
        <div class="mr-4 flex-grow font-bold sm:text-lg whitespace-no-wrap flex items-center mb-1 sm:mb-0">
          {data.case && <Case {...data.case} />}
          {data.search_query && <Search search_query={data.search_query} />}
          {data.address && <Address {...data.address} />}
          {data.entity && <Entity {...data.entity} />}
        </div>
        <div>
          <div class="flex justify-end sm:justify-between items-center w-full sm:w-auto">
            {data.address && (
              <div class="mr-2 sm:mr-4">
                <SelectWidget
                  value={data.radius || 0}
                  onChange={onChangeRadius}
                  isDisabled={isLoading}
                >
                  <Fragment>
                    <option value={0}>0m</option>
                    <option value={100}>+ 100m</option>
                    <option value={300}>+ 300m</option>
                    <option value={500}>+ 500m</option>
                  </Fragment>
                </SelectWidget>
              </div>
            )}
            <SelectWidget
              value={value}
              onChange={onChange}
              isDisabled={isLoading}
            >
              <Fragment>
                <option value="never">Afvirkja</option>
                <option value="immediate">Strax</option>
                <option value="weekly">Vikuleg</option>
              </Fragment>
            </SelectWidget>
            <button
              class="ml-3 sm:ml-6 text-gray-500 flex-grow sm:flex-grow-0 flex justify-end"
              onClick={(event) => {
                !isLoading && onDelete(event);
              }}
            >
              <TrashFill />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export const Subscriptions = () => {
  const [subs, setSubs] = useState([]);
  useEffect(async () => {
    const subs = await api.getSubscriptions().then((response) => {
      return response.data;
    });
    setSubs(subs);
  }, []);
  if (!subs.length) {
    return (
      <div>
        <SubscriptionLoading />
        <SubscriptionLoading />
        <SubscriptionLoading />
      </div>
    );
  }
  return (
    <div>
      {subs.map((sub) => {
        return <Subscription key={sub.id} subscription={sub} />;
      })}
    </div>
  );
};

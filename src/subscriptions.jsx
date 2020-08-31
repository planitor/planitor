import { Fragment, h } from "preact";
import { useState, useRef, useEffect } from "preact/hooks";
import { api } from "./api";
import { TrashFill } from "./symbols.jsx";

const Case = ({ serial, id }) => {
  return <a href={`/cases/${id}`}>{serial}</a>;
};

const Search = ({ search_query }) => {
  return <a href={`/leit?q=${search_query}`}>„{search_query}“</a>;
};

const Address = ({ name, hnitnum, radius }) => {
  return (
    <a href={`/hnit/${hnitnum}`}>
      {name} {radius}
    </a>
  );
};

const SelectWidget = ({ value, onChange, isDisabled, children }) => {
  return (
    <div class="inline-block relative text-sm sm:text-base">
      <select
        value={value}
        onChange={onChange}
        disabled={isDisabled}
        class="block appearance-none w-full border border-gray-400 hover:border-gray-500 px-1 sm:px-4 py-1 sm:py-2 pr-8 mr-3 rounded shadow leading-tight focus:outline-none focus:shadow-outline"
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

const Entity = ({ kennitala, name }) => {
  return <a href={`/f/${kennitala}`}>{name}</a>;
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
    const active = value !== "never";
    const immediate = value === "immediate";
    setLoading(true);
    const data = await api
      .updateSubscription(id, active, immediate)
      .then((response) => {
        return response.data;
      });
    setLoading(false);
    setData(data);
  };

  return (
    <div class="rounded-lg shadow-sm p-4 w-full bg-white mb-4">
      <div class="flex flex-row align-middle">
        <div class="mr-4 flex-grow font-bold py-1 text-sm sm:text-lg whitespace-no-wrap">
          {subscription.case && <Case {...subscription.case} />}
          {subscription.search_query && (
            <Search search_query={subscription.search_query} />
          )}
          {subscription.address && (
            <Address
              radius={subscription.radius || null}
              {...subscription.address}
            />
          )}
          {subscription.entity && <Entity {...subscription.entity} />}
        </div>
        <div>
          <div class="flex justify-between items-center w-full">
            <SelectWidget
              isDisabled={isLoading}
              value={value}
              onChange={onChange}
            >
              <Fragment>
                <option value="never">Afvirkja</option>
                <option value="immediate">Strax</option>
                <option value="weekly">Vikuleg</option>
              </Fragment>
            </SelectWidget>
            <button
              class="ml-3 sm:ml-6 text-gray-500"
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

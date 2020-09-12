import { Fragment, h } from "preact";
import { useState, useEffect } from "preact/hooks";
import { api } from "./api";
import { TrashFill } from "./symbols.jsx";
import { groupBy, keyBy } from "lodash";

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

const Case = ({ serial, id, council }) => {
  return (
    <a href={`/cases/${id}`} class="block">
      <div>{serial}</div>
      <div class="font-normal text-gray-700 text-xs">{council.name}</div>
    </a>
  );
  return <a href={`/cases/${id}`}>{serial}</a>;
};

const Search = ({ search_query }) => {
  return <a href={`/leit?q=${search_query}`}>„{search_query}“</a>;
};

const Address = ({ name, hnitnum, stadur_nf }) => {
  return (
    <a href={`/heimilisfong/${hnitnum}`} class="block">
      <div>{name}</div>
      <div class="font-normal text-gray-700 text-xs">{stadur_nf}</div>
    </a>
  );
};

const Entity = ({ kennitala, name }) => {
  return (
    <a href={`/f/${kennitala}`} class="block">
      <div>{name}</div>
      <div class="font-normal text-gray-700 text-xs">kt. {kennitala}</div>
    </a>
  );
};

const SelectCouncils = ({ councils, onChangeCouncils }) => {
  const onClick = (_name, _selected) => {
    onChangeCouncils(
      councils.map(({ name, selected }) => {
        return { name: name, selected: _name === name ? _selected : selected };
      })
    );
  };

  return (
    <div class="">
      {councils.map(({ label, name, selected }) => {
        return (
          <div
            class="text-xs"
            onClick={(event) => {
              onClick(name, !selected);
            }}
          >
            <div class={selected && "font-bold"}>{label}</div>
          </div>
        );
      })}
    </div>
  );
};

const getCouncils = (subscription, councilTypes, municipalities) => {
  /* A subscription usually monitors across all council types. The user
     can narrow it down to a few types of councils. Furthermore, to make
     the UX better, the actual council names are displayed if the
     subscription type is bound to an area (therefore bound to a municipality).
  */

  let councils = [];

  const muniById = keyBy(municipalities, (m) => {
    return m.id;
  });

  const subCouncilTypesByName = keyBy(subscription.council_types, (c) => {
    const [_, __, name] = c;
    return name;
  });

  for (const councilType of councilTypes) {
    const [enumSlug, enumLabel, enumName] = councilType;
    const selected =
      !!subCouncilTypesByName[enumName] || subscription.council_types === null;

    let municipality;
    if (subscription.case)
      municipality = muniById[subscription.case.council.municipality.id];
    if (subscription.address)
      municipality = muniById[subscription.address.municipality.id];
    let label = enumLabel;
    if (municipality) {
      // For cases and addresses we can use the slightly more specific
      // name of the council for this municipality - so instead of a generic
      // "Skipulagsráð" we can have "Skipulags- og samgönguráð" if that’s the
      // name in the relavant municipality. Note that not all monitored
      // entities are bound to municipalities, hence the if/else above for
      // case/address subscriptions.
      for (const council of municipality.councils) {
        const [_, __, municipalityCouncilType] = council.council_type;
        if (municipalityCouncilType === enumName) {
          label = council.name;
        }
      }
    }
    councils.push({
      selected: selected,
      name: enumName,
      label: label,
    });
  }

  return councils;
};

const Subscription = ({ subscription, municipalities, councilTypes }) => {
  const [isLoading, setLoading] = useState(false);
  const [isDeleted, setDeleted] = useState(false);
  const [data, setData] = useState(subscription);

  if (isDeleted) return null;

  const { id, active, immediate } = data;
  let value = immediate ? "immediate" : "weekly";

  if (!active) {
    value = "never";
  }

  const councils = getCouncils(data, councilTypes, municipalities);

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

  const onChangeCouncils = async (councils) => {
    setLoading(true);
    const responseData = await api
      .updateSubscription(id, { councils: councils })
      .then((response) => {
        return response.data;
      });
    setLoading(false);
    setData(responseData);
  };

  const onChangeDelivery = async (event) => {
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
    <div class="pb-2 mb-2 sm:mb-0 sm:p-4 w-full">
      <div class="flex flex-col md:flex-row align-middle">
        <div class="mr-4 flex-grow font-bold sm:text-lg whitespace-no-wrap flex items-center mb-1 sm:mb-0">
          {data.case && <Case {...data.case} />}
          {data.search_query && <Search search_query={data.search_query} />}
          {data.address && <Address {...data.address} />}
          {data.entity && <Entity {...data.entity} />}
        </div>
        <div>
          <div class="flex justify-end sm:justify-between items-center w-full sm:w-auto">
            <SelectCouncils
              councils={councils}
              onChangeCouncils={onChangeCouncils}
            />
            {data.address && (
              <div class="mr-2 sm:mr-4">
                <SelectWidget
                  value={data.radius || 0}
                  onChange={onChangeRadius}
                  isDisabled={isLoading}
                >
                  <Fragment>
                    <option value={0}>0m</option>
                    <option value={50}>+ 50m</option>
                    <option value={100}>+ 100m</option>
                    <option value={300}>+ 300m</option>
                    <option value={500}>+ 500m</option>
                  </Fragment>
                </SelectWidget>
              </div>
            )}
            <SelectWidget
              value={value}
              onChange={onChangeDelivery}
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

const Group = ({ type, subscriptions, ...props }) => {
  return (
    <div class="mb-4 sm:mb-8">
      <div class="mb-4 sm:px-5 uppercase font-light tracking-wider text-xs">
        {type}
      </div>
      <div class="sm:rounded-lg sm:shadow-sm pb-2 sm:p-1 w-full sm:bg-white">
        {subscriptions.map((sub) => {
          return <Subscription key={sub.id} subscription={sub} {...props} />;
        })}
      </div>
    </div>
  );
};

export const Subscriptions = () => {
  const [subscriptions, setSubscriptions] = useState([]);
  const [councilTypes, setCouncilTypes] = useState([]);
  const [municipalities, setMunicipalities] = useState([]);

  useEffect(async () => {
    // Municipalities objects are needed to render all municipality options
    // in address subscription widgets, specifically where the user can pick
    // and choose the councils being monitored
    const responses = await Promise.all([
      api.getSubscriptions(),
      api.getCouncilTypes(),
      api.getMunicipalities(),
    ]).then(
      ([
        subscriptionResponse,
        councilTypesResponse,
        municipalitiesResponse,
      ]) => {
        setSubscriptions(subscriptionResponse.data);
        setCouncilTypes(councilTypesResponse.data);
        setMunicipalities(municipalitiesResponse.data);
      }
    );
  }, []);

  if (!subscriptions.length) {
    return (
      <div>
        <SubscriptionLoading />
        <SubscriptionLoading />
        <SubscriptionLoading />
      </div>
    );
  }

  let types = {};

  let groups = Object.entries(
    groupBy(subscriptions, (subscription) => {
      types[subscription.type[0]] = subscription.type;
      return subscription.type[0];
    })
  );

  groups.sort(([key, _]) => {
    return key;
  });

  return (
    <div>
      {groups.map(([type, subscriptions]) => {
        return (
          <Group
            subscriptions={subscriptions}
            councilTypes={councilTypes}
            municipalities={municipalities}
            type={types[type][1]}
          />
        );
      })}
    </div>
  );
};

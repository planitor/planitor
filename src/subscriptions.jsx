import { Fragment, h, render } from "preact";
import { useState, useEffect } from "preact/hooks";
import { groupBy, keyBy } from "lodash";

import { openModal } from "./modals";
import { api } from "./api";
import { Ellipsis, TrashFill } from "./symbols.jsx";
import { SelectWidget } from "./forms/widgets.jsx";

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

const Case = ({ serial, id, municipality }) => {
  return (
    <a href={`/cases/${id}`} class="block">
      <div>{serial}</div>
      {municipality && (
        <div class="font-normal text-gray-700 text-xs">{municipality.name}</div>
      )}
    </a>
  );
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

const SelectCouncils = ({ councils, isDisabled, onChangeCouncils }) => {
  const onClick = (_name, _selected) => {
    onChangeCouncils(
      councils
        .map(({ name, selected }) => {
          return {
            name: name,
            selected: _name === name ? _selected : selected,
          };
        })
        .filter(({ selected }) => {
          return selected;
        })
    );
  };

  return (
    <div>
      {councils.map(({ label, name, selected }) => {
        return (
          <label
            class="flex items-center text-left"
            onClick={(event) => {
              onClick(name, !selected);
            }}
          >
            <input
              type="checkbox"
              disabled={isDisabled}
              checked={selected && "checked"}
            />
            <div class="flex-grow ml-2">{label}</div>
          </label>
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
      municipality = muniById[subscription.case.municipality.id];
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
          councils.push({
            selected: selected,
            name: enumName,
            label: council.name,
          });
        }
      }
    } else {
      councils.push({
        selected: selected,
        name: enumName,
        label: label,
      });
    }
  }

  return councils;
};

const Settings = ({
  parentData,
  setParentData,
  setDeleted,
  councilTypes,
  municipalities,
  closeModal,
}) => {
  const [data, setChildData] = useState(parentData);
  const [isLoading, setLoading] = useState(false);

  const councils = getCouncils(data, councilTypes, municipalities);

  const setData = (data) => {
    // A dirty way to connect two Preact trees together, this one is inside a modal window
    // so not inside the component tree and a part of another `render` call.
    setChildData(data);
    setParentData(data);
  };

  const { id, active, immediate } = data;
  let delivery = immediate ? "immediate" : "weekly";

  if (!active) {
    delivery = "never";
  }

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
    closeModal();
  };

  const onChangeCouncils = async (councils) => {
    setLoading(true);
    const responseData = await api
      .updateSubscription(id, { council_types: councils })
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
    <div class="">
      {data.address && (
        <div class="flex items-center py-4 sm:py-6 border-b border-gray-300">
          <div class="flex-grow font-bold">Radíus</div>
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
      <div class="flex items-center py-4 sm:py-6 border-b border-gray-300">
        <div class="flex-grow font-bold">Afhending</div>
        <SelectWidget
          value={delivery}
          onChange={onChangeDelivery}
          isDisabled={isLoading}
        >
          <Fragment>
            <option value="never">Afvirkja</option>
            <option value="immediate">Strax</option>
            <option value="weekly">Vikuleg</option>
          </Fragment>
        </SelectWidget>
      </div>
      <div class="py-4 items-center sm:py-6 border-b border-gray-300">
        <div class="font-bold mb-1">Fundargerðir</div>
        <SelectCouncils
          councils={councils}
          isDisabled={isLoading}
          onChangeCouncils={onChangeCouncils}
        />
      </div>
      <div class="py-4 sm:py-6 text-center">
        <button
          class="text-planitor-red font-bold"
          onClick={(event) => {
            !isLoading && onDelete(event);
          }}
        >
          Eyða
        </button>
      </div>
    </div>
  );
};

const Subscription = ({ subscription, municipalities, councilTypes }) => {
  const [isDeleted, setDeleted] = useState(false);
  const [data, setData] = useState(subscription);

  if (isDeleted) return null;

  const openSettings = (event) => {
    event.stopPropagation();
    const [modalRender, closeModal] = openModal();

    modalRender(
      <Settings
        parentData={data}
        setParentData={setData}
        setDeleted={setDeleted}
        councilTypes={councilTypes}
        municipalities={municipalities}
        closeModal={closeModal}
      />
    );
  };

  return (
    <div class="pb-2 mb-2 sm:mb-0 sm:p-4 w-full">
      <div class="flex align-middle">
        <div class="mr-4 flex-grow font-bold sm:text-lg whitespace-no-wrap flex items-center mb-1 sm:mb-0">
          {data.case && <Case {...data.case} />}
          {data.search_query && <Search search_query={data.search_query} />}
          {data.address && <Address {...data.address} />}
          {data.entity && <Entity {...data.entity} />}
        </div>
        <div>
          <button onClick={openSettings}>
            <Ellipsis />
          </button>
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

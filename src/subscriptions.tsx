import { keyBy } from "lodash-es";
import { Fragment } from "react";

import { useQuery } from "react-query";
import {
  Case as CaseModel,
  CouncilTypeEnum,
  Municipality,
  Subscription as SubscriptionModel,
  SubscriptionTypeEnum,
  useDeleteSubscription,
  useGetEnums,
  useGetMunicipalities,
  useGetSubscriptions,
  useUpdateSubscription,
} from "./api/types";
import { Select } from "./forms/widgets";
import { openModal } from "./modals";
import { Ellipsis } from "./symbols";

const SubscriptionLoading = () => {
  return (
    <div className="rounded-lg shadow-sm p-4 w-full bg-white mb-4">
      <div className="animate-pulse flex flex-row">
        <div className="bg-gray-400 rounded w-3/4 mr-4 h-8"></div>
        <div className="bg-gray-400 rounded w-1/4 mr-4 h-8"></div>
        <div className="bg-gray-400 rounded w-16 h-8"></div>
      </div>
    </div>
  );
};

const Case = ({ serial, id, municipality }: CaseModel) => {
  return (
    <a href={`/cases/${id}`} className="block">
      <div>{serial}</div>
      {municipality && (
        <div className="font-normal text-gray-700 text-xs">
          {municipality.name}
        </div>
      )}
    </a>
  );
};

const Search = ({ search_query }) => {
  return <a href={`/leit?q=${search_query}`}>„{search_query}“</a>;
};

const Address = ({ name, hnitnum, stadur_nf }) => {
  return (
    <a href={`/heimilisfong/${hnitnum}`} className="block">
      <div>{name}</div>
      <div className="font-normal text-gray-700 text-xs">{stadur_nf}</div>
    </a>
  );
};

const Entity = ({ kennitala, name }) => {
  return (
    <a href={`/f/${kennitala}`} className="block">
      <div>{name}</div>
      <div className="font-normal text-gray-700 text-xs">kt. {kennitala}</div>
    </a>
  );
};

const SelectCouncils = ({ councils, disabled, onChangeCouncils }) => {
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
        .map(({ name }) => {
          return name;
        })
    );
  };

  return (
    <div>
      {councils.map(({ label, name, selected }) => {
        return (
          <label
            className="flex items-center text-left"
            onClick={(event) => {
              onClick(name, !selected);
            }}
          >
            <input type="checkbox" disabled={disabled} checked={selected} />
            <div className="flex-grow ml-2">{label}</div>
          </label>
        );
      })}
    </div>
  );
};

const getCouncils = (
  subscription: SubscriptionModel,
  councilTypes: Map<CouncilTypeEnum, string>,
  municipalities: Municipality[]
) => {
  /* A subscription usually monitors across all council types. The user
     can narrow it down to a few types of councils. Furthermore, to make
     the UX better, the actual council names are displayed if the
     subscription type is bound to an area (therefore bound to a municipality).
  */

  let councils = [];

  const muniById = keyBy(municipalities, (m) => {
    return m.id;
  });

  let municipality;
  if (subscription.case)
    municipality = muniById[subscription.case.municipality.id];
  if (subscription.address)
    municipality = muniById[subscription.address.municipality.id];

  Array.from(councilTypes).forEach(([enumSlug, enumLabel]) => {
    const selected =
      subscription.council_types === null ||
      subscription.council_types.indexOf(enumSlug) > -1;
    let label = enumLabel;

    if (municipality) {
      // For cases and addresses we can use the slightly more specific
      // name of the council for this municipality - so instead of a generic
      // "Skipulagsráð" we can have "Skipulags- og samgönguráð" if that’s the
      // name in the relavant municipality. Note that not all monitored
      // entities are bound to municipalities, hence the if/else above for
      // case/address subscriptions.
      for (const council of municipality.councils) {
        if (council.council_type === enumSlug) {
          councils.push({
            selected: selected,
            name: enumSlug,
            label: council.name,
          });
        }
      }
    } else {
      councils.push({
        selected: selected,
        name: enumSlug,
        label: label,
      });
    }
  });

  return councils;
};

const Settings = ({
  subscription,
  councilTypes,
  municipalities,
  closeModal,
}: {
  subscription: SubscriptionModel;
  councilTypes: Map<CouncilTypeEnum, string>;
  municipalities: Municipality[];
  closeModal: () => void;
}) => {
  const { mutateAsync: deleteSubscription, isLoading: isLoadingDelete } =
    useDeleteSubscription();
  const { mutateAsync: updateSubscription, isLoading: isLoadingUpdate } =
    useUpdateSubscription();

  const isLoading = isLoadingDelete || isLoadingUpdate;

  const councils = getCouncils(subscription, councilTypes, municipalities);

  const { id, active, immediate } = subscription;
  let delivery = immediate ? "immediate" : "weekly";

  if (!active) {
    delivery = "never";
  }

  const onDelete = async () => {
    const isConfirmed = confirm(
      "Ertu viss um að þú viljir fjárlægja þennan vaktara?"
    );
    if (!isConfirmed) return;
    await deleteSubscription({ id });
    closeModal();
  };

  const onChangeCouncils = async (council_types: CouncilTypeEnum[]) => {
    await updateSubscription({ id, data: { council_types } });
  };

  const onChangeDelivery = async (event) => {
    const { value } = event.target;
    await updateSubscription({
      id,
      data: {
        active: value !== "never",
        immediate: value === "immediate",
      },
    });
  };

  const onChangeRadius = async (event) => {
    const { value } = event.target;
    await updateSubscription({ id, data: { radius: Number(value) } });
  };

  return (
    <div className="">
      {subscription.address && (
        <div className="grid grid-cols-2 items-center py-4 sm:py-6 border-gray-300">
          <div className="font-bold">Radíus</div>
          <Select
            value={subscription.radius || 0}
            onChange={onChangeRadius}
            disabled={isLoading}
          >
            <Fragment>
              <option value={0}>0m</option>
              <option value={50}>+ 50m</option>
              <option value={100}>+ 100m</option>
              <option value={300}>+ 300m</option>
              <option value={500}>+ 500m</option>
            </Fragment>
          </Select>
        </div>
      )}
      <div className="grid grid-cols-2 items-center py-4 sm:py-6 border-gray-300">
        <div className="font-bold">Afhending</div>
        <Select
          value={delivery}
          onChange={onChangeDelivery}
          disabled={isLoading}
        >
          <Fragment>
            <option value="never">Afvirkja</option>
            <option value="immediate">Strax</option>
            <option value="weekly">Vikuleg</option>
          </Fragment>
        </Select>
      </div>
      <div className="py-4 items-center sm:py-6 border-gray-300">
        <div className="font-bold mb-1">Fundargerðir</div>
        <SelectCouncils
          councils={councils}
          disabled={isLoading}
          onChangeCouncils={onChangeCouncils}
        />
      </div>
      <div className="py-4 sm:py-6 text-center">
        <button
          className="text-planitor-red font-bold rounded-lg bg-red-200 p-3 w-full"
          onClick={() => {
            !isLoading && onDelete();
          }}
        >
          Eyða
        </button>
      </div>
    </div>
  );
};

const Subscription = ({
  subscription,
  municipalities,
  councilTypes,
}: {
  subscription: SubscriptionModel;
  municipalities: Municipality[];
  councilTypes: Map<CouncilTypeEnum, string>;
}) => {
  const openSettings = (event) => {
    event.stopPropagation();
    const [modalRender, closeModal] = openModal();

    modalRender(
      <Settings
        subscription={subscription}
        councilTypes={councilTypes}
        municipalities={municipalities}
        closeModal={closeModal}
      />
    );
  };

  return (
    <div className="pb-2 mb-2 sm:mb-0 sm:p-4 w-full">
      <div className="flex align-middle">
        <div className="mr-4 flex-grow font-bold sm:text-lg whitespace-no-wrap flex items-center mb-1 sm:mb-0">
          {subscription.case && <Case {...subscription.case} />}
          {subscription.search_query && (
            <Search search_query={subscription.search_query} />
          )}
          {subscription.address && <Address {...subscription.address} />}
          {subscription.entity && <Entity {...subscription.entity} />}
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

const Group = ({
  label,
  subscriptions,
  councilTypes,
  municipalities,
}: {
  label: string;
  subscriptions: SubscriptionModel[];
  municipalities: Municipality[];
  councilTypes: Map<CouncilTypeEnum, string>;
}) => {
  return (
    <div className="mb-4 sm:mb-8">
      <div className="mb-4 sm:px-5 uppercase font-light tracking-wider text-xs">
        {label}
      </div>
      <div className="sm:rounded-lg sm:shadow-sm pb-2 sm:p-1 w-full sm:bg-white">
        {subscriptions.map((sub) => {
          return (
            <Subscription
              key={sub.id}
              subscription={sub}
              councilTypes={councilTypes}
              municipalities={municipalities}
            />
          );
        })}
      </div>
    </div>
  );
};

export const Subscriptions = () => {
  const subs = useGetSubscriptions();
  const munis = useGetMunicipalities();
  const enums = useGetEnums();

  const isLoading = subs.isLoading || munis.isLoading || enums.isLoading;

  if (isLoading) {
    return (
      <div>
        <SubscriptionLoading key={"1"} />
        <SubscriptionLoading key={"2"} />
        <SubscriptionLoading key={"3"} />
      </div>
    );
  }

  const subscriptionTypes = new Map<SubscriptionTypeEnum, string>(
    enums.data.subscription_types as [SubscriptionTypeEnum, string][]
  );
  const councilTypes = new Map<CouncilTypeEnum, string>(
    enums.data.council_types as [CouncilTypeEnum, string][]
  );

  const subscriptionMap = subs.data.reduce((m, sub) => {
    m.has(sub.type) ? m.get(sub.type).push(sub) : m.set(sub.type, [sub]);
    return m;
  }, new Map<SubscriptionTypeEnum, typeof subs.data>());

  return (
    <div>
      {Array.from(subscriptionMap).map(([type, subscriptions]) => {
        return (
          <Group
            key={type}
            subscriptions={subs.data}
            councilTypes={councilTypes}
            municipalities={munis.data}
            label={subscriptionTypes.get(type)}
          />
        );
      })}
    </div>
  );
};

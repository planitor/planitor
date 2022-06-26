import { useField, useForm } from "@shopify/react-form";
import { keyBy } from "lodash-es";
import { Fragment } from "react";

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
import { Primary, Select } from "./forms/widgets";
import { openModal } from "./modals";
import { queryClient } from "./query";
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

type MunicipalityCouncil = {
  selected: boolean;
  name: CouncilTypeEnum;
  label: string;
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

  let councils: MunicipalityCouncil[] = [];

  const muniById = keyBy(municipalities, (m) => {
    return m.id;
  });

  let municipality: Municipality;
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

enum DeliveryOptions {
  IMMEDIATE = "immediate",
  WEEKLY = "weekly",
  NEVER = "never",
}

function Form({
  subscription,
  councils,
}: {
  subscription: SubscriptionModel;
  councils: MunicipalityCouncil[];
}) {
  const { mutateAsync } = useUpdateSubscription({
    mutation: {
      onSuccess() {
        queryClient.invalidateQueries([["/api/subscriptions"]]);
      },
    },
  });

  const { fields, submitting, submit, dirty } = useForm({
    fields: {
      delivery: useField<DeliveryOptions>(
        subscription.active
          ? subscription.immediate
            ? DeliveryOptions.IMMEDIATE
            : DeliveryOptions.WEEKLY
          : DeliveryOptions.NEVER
      ),
      councils: useField<Set<CouncilTypeEnum>>(
        new Set(subscription.council_types)
      ),
      radius: useField<number>(subscription.radius || 0),
    },
    async onSubmit(form) {
      await mutateAsync({
        id: subscription.id,
        data: {
          active: form.delivery !== DeliveryOptions.NEVER,
          immediate: form.delivery === DeliveryOptions.IMMEDIATE,
          council_types: [...form.councils],
          radius: subscription.address ? Number(form.radius) : undefined,
        },
      });
      return { status: "success" };
    },
  });
  return (
    <form onSubmit={submit}>
      <div className="grid grid-cols-2 gap-4 items-center py-4 sm:py-6 border-gray-300">
        {subscription.address && (
          <>
            <div className="font-bold">Radíus</div>
            <Select
              value={fields.radius.value}
              onChange={(event) =>
                fields.radius.onChange(parseInt(event.target.value, 10))
              }
            >
              <option value={0}>0m</option>
              <option value={50}>+ 50m</option>
              <option value={100}>+ 100m</option>
              <option value={300}>+ 300m</option>
              <option value={500}>+ 500m</option>
            </Select>
          </>
        )}
        <div className="font-bold mb-1">Afhending</div>
        <Select
          value={fields.delivery.value}
          onChange={(event) =>
            fields.delivery.onChange(event.target.value as DeliveryOptions)
          }
        >
          <option value="never">Afvirkja</option>
          <option value="immediate">Strax</option>
          <option value="weekly">Vikuleg</option>
        </Select>
        <div className="font-bold mb-1">Fundargerðir</div>
        <div>
          {councils.map((council) => (
            <label
              className="flex items-center mb-2 focus-within:focus:ring-powder-default focus-within:focus:ring-2"
              key={council.name}
            >
              <input
                type="checkbox"
                className="rounded-sm mr-2 border-gray-400 cursor-pointer"
                checked={fields.councils.value.has(council.name)}
                onChange={(event) => {
                  const set = new Set<CouncilTypeEnum>(fields.councils.value);
                  if (event.target.checked) {
                    set.add(council.name);
                  } else {
                    set.delete(council.name);
                  }
                  fields.councils.onChange(set);
                }}
              />
              {council.label}
            </label>
          ))}
        </div>
      </div>
      <div className="pb-4 sm:pb-6 text-center">
        <Primary type="submit" disabled={!dirty || submitting}>
          Vista breytingar
        </Primary>
      </div>
    </form>
  );
}

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
  const { mutateAsync: deleteSubscription, isLoading } = useDeleteSubscription({
    mutation: {
      onSuccess() {
        queryClient.invalidateQueries([["/api/subscriptions"]]);
      },
    },
  });

  const councils = getCouncils(subscription, councilTypes, municipalities);

  const onDelete = async () => {
    const isConfirmed = confirm(
      "Ertu viss um að þú viljir eyða þessum vaktara?"
    );
    if (!isConfirmed) return;
    await deleteSubscription({ id: subscription.id });
    closeModal();
  };

  return (
    <div className="">
      <Form subscription={subscription} councils={councils} />
      <div className="pt-4 sm:pt-6 text-center border-t border-gray-300">
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

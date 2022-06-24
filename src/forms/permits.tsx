import { Fragment, useEffect, useState } from "react";
import {
  BuildingTypeEnum,
  PermitTypeEnum,
  useGetEnums,
  useGetPermit,
  useUpdatePermit,
} from "../api/types";

import { Select, NumberInput, TextInput } from "../forms/widgets";

export const PermitForm = ({ minuteId }) => {
  const { data } = useGetPermit(minuteId);
  const { data: enums } = useGetEnums();
  const { mutateAsync } = useUpdatePermit();
  const [form, setForm] = useState({});

  enums.building_types as [BuildingTypeEnum, string][];
  enums.permit_types as [PermitTypeEnum, string][];

  if (!data || !enums) {
    return <div>Hleð ...</div>;
  }

  const created = !!data.created;

  const getSubmitData = ({
    units,
    area_added,
    area_subtracted,
    permit_type,
    building_type,
  }) => {
    return {
      units: Number(units) || null,
      area_added: Number(area_added) || null,
      area_subtracted: Number(area_subtracted) || null,
      permit_type: permit_type,
      building_type: building_type,
    };
  };

  const onSubmit = async (event) => {
    const response = await mutateAsync({ minuteId, data: getSubmitData(form) });
  };

  return (
    <div>
      <div className="mb-3 grid gap-2 grid-cols-2">
        <div>
          <label className="text-xs block mb-1">Tegund leyfis</label>
          <Select
            value={form.permit_type}
            onChange={(e) => {
              setForm({
                ...form,
                permit_type: e.target.value || null,
              });
            }}
            disabled={form.isLoading}
          >
            <Fragment>
              <option value="">Ekkert valið</option>
              {enums.permit_types.map(([slug, label]) => {
                return <option value={slug}>{label}</option>;
              })}
            </Fragment>
          </Select>
        </div>
        <div>
          <label className="text-xs block mb-1">Tegund byggingar</label>
          <Select
            value={form.building_type}
            onChange={(e) => {
              setForm({
                ...form,
                building_type: e.target.value || null,
              });
            }}
            disabled={form.isLoading}
          >
            <Fragment>
              <option value="">Ekkert valið</option>
              {enums.building_types.map(([slug, label]) => {
                return <option value={slug}>{label}</option>;
              })}
            </Fragment>
          </Select>
        </div>
      </div>
      <div className="mb-4 grid gap-2 grid-cols-3">
        <div>
          <label className="text-xs block mb-1">Einingar</label>
          <NumberInput
            value={form.units}
            onInput={(e: Event) =>
              setForm({
                ...form,
                units: e.target?.value,
              })
            }
          />
        </div>
        <div>
          <label className="text-xs block mb-1">Viðbætt</label>
          <TextInput
            value={form.area_added}
            onInput={(e) => {
              setForm({
                ...form,
                area_added: e.target.value,
              });
            }}
          />
        </div>
        <div>
          <label className="text-xs block mb-1">Niðurrif</label>
          <TextInput
            value={form.area_subtracted}
            // pattern="[0-9]+([\.][0-9])?"
            onInput={(e) =>
              setForm({
                ...form,
                area_subtracted: e.target.value,
              })
            }
          />
        </div>
      </div>
      <div className="flex items-baseline mb-2">
        <div className="flex-grow text-right text-gray-500 pr-4">
          {(created && "Vistað") || "Ekkert leyfi vistað"}
        </div>
        <div className="">
          <button
            className="btn btn-small"
            disabled={isLoading}
            onClick={onSubmit}
          >
            {(!created && "Vista") || "Uppfæra"}
          </button>
        </div>
      </div>
    </div>
  );
};

import { Fragment, h, render } from "preact";
import { useEffect, useState } from "preact/hooks";

import { Select, NumberInput, TextInput } from "../forms/widgets.jsx";
import { api } from "../api";

export const PermitForm = ({ minuteId }) => {
  const [form, setForm] = useState({
    data: null,
    isLoading: false,
    error: null,
  });
  const [enums, setEnums] = useState([]);

  useEffect(async () => {
    // Municipalities objects are needed to render all municipality options
    // in address subscription widgets, specifically where the user can pick
    // and choose the councils being monitored
    const responses = await Promise.all([
      api.getPermit(minuteId),
      api.getEnums(),
    ]).then(([permitResponse, enumsResponse]) => {
      setForm({ ...form, data: permitResponse.data });
      setEnums(enumsResponse.data);
    });
  }, []);

  if (form.data === null) {
    return <div>Hleð ...</div>;
  }

  const created = !!form.data.created;

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
    setForm({ ...form, isLoading: true });
    const response = await api.putPermit(minuteId, getSubmitData(form.data));
    setForm({ ...form, isLoading: false, data: response.data });
  };

  return (
    <div>
      <div class="mb-3 grid gap-2 grid-cols-2">
        <div>
          <label class="text-xs block mb-1">Tegund leyfis</label>
          <Select
            value={form.data.permit_type}
            onChange={(e) => {
              setForm({
                ...form,
                data: { ...form.data, permit_type: e.target.value || null },
              });
            }}
            isDisabled={form.isLoading}
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
          <label class="text-xs block mb-1">Tegund byggingar</label>
          <Select
            value={form.data.building_type}
            onChange={(e) => {
              setForm({
                ...form,
                data: { ...form.data, building_type: e.target.value || null },
              });
            }}
            isDisabled={form.isLoading}
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
      <div class="mb-4 grid gap-2 grid-cols-3">
        <div>
          <label class="text-xs block mb-1">Einingar</label>
          <NumberInput
            value={form.data.units}
            onInput={(e) =>
              setForm({
                ...form,
                data: { ...form.data, units: e.target.value },
              })
            }
          />
        </div>
        <div>
          <label class="text-xs block mb-1">Viðbætt</label>
          <TextInput
            value={form.data.area_added}
            onInput={(e) => {
              setForm({
                ...form,
                data: { ...form.data, area_added: e.target.value },
              });
            }}
          />
        </div>
        <div>
          <label class="text-xs block mb-1">Niðurrif</label>
          <TextInput
            value={form.data.area_subtracted}
            // pattern="[0-9]+([\.][0-9])?"
            onInput={(e) =>
              setForm({
                ...form,
                data: { ...form.data, area_subtracted: e.target.value },
              })
            }
          />
        </div>
      </div>
      <div class="flex items-baseline mb-2">
        <div class="flex-grow text-right text-gray-500 pr-4">
          {(created && "Vistað") || "Ekkert leyfi vistað"}
        </div>
        <div class="">
          <button
            class="btn btn-small"
            disabled={form.isLoading}
            onClick={onSubmit}
          >
            {(!created && "Vista") || "Uppfæra"}
          </button>
        </div>
      </div>
    </div>
  );
};

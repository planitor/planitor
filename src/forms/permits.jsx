import { Fragment, h, render } from "preact";
import { useEffect, useState } from "preact/hooks";

import { Select, TextInput } from "../forms/widgets.jsx";
import { api } from "../api";

export const PermitForm = ({ minuteId }) => {
  const [form, setForm] = useState({
    data: null,
    isLoading: false,
    error: null,
  });
  const [permitType, setPermitType] = useState([]);
  const [buildingType, setBuildingType] = useState([]);
  const [permitTypes, setPermitTypes] = useState([]);
  const [buildingTypes, setBuildingTypes] = useState([]);

  useEffect(async () => {
    // Municipalities objects are needed to render all municipality options
    // in address subscription widgets, specifically where the user can pick
    // and choose the councils being monitored
    const responses = await Promise.all([
      api.getPermit(minuteId),
      api.getPermitTypes(),
      api.getBuildingTypes(),
    ]).then(([permitResponse, permitTypesResponse, buildingTypesResponse]) => {
      setForm({ ...form, data: permitResponse.data });
      setPermitType(permitResponse.data.permit_type && permitResponse.data.permit_type[0] || null);
      setPermitTypes(permitTypesResponse.data);
      setBuildingType(permitResponse.data.building_type && permitResponse.data.building_type[0] || null);
      setBuildingTypes(buildingTypesResponse.data);
    });
  }, []);

  if (form.data === null) {
    return <div>Hleð ...</div>;
  }

  const created = !!form.data.created;

  const onChangeBuildingType = (event) => {
    setBuildingType(event.target.value || null);
  };

  const onChangePermitType = (event) => {
    setPermitType(event.target.value || null);
  };

  const getSubmitData = ({ units, area_added, area_subtracted }) => {
    return {
      units: units || null,
      area_added: area_added || null,
      area_subtracted: area_subtracted || null,
      permit_type: permitType,
      building_type: buildingType,
    };
  };

  const onSubmit = async (event) => {
    setForm({ ...form, isLoading: true });
    const response = await api.putPermit(minuteId, getSubmitData(form.data));
    setForm({ ...form, isLoading: false, data: response.data });
  };

  return (
    <div>
      <div class="mb-2 grid gap-2 grid-cols-2">
        <div>
          <label class="text-sm block mb-1">Tegund leyfis</label>
          <Select
            value={permitType}
            onChange={onChangePermitType}
            isDisabled={form.isLoading}
          >
            <Fragment>
              <option value="">Ekkert valið</option>
              {permitTypes.map(([slug, label]) => {
                return <option value={slug}>{label}</option>;
              })}
            </Fragment>
          </Select>
        </div>
        <div>
          <label class="text-sm block mb-1">Tegund byggingar</label>
          <Select
            value={buildingType}
            onChange={onChangeBuildingType}
            isDisabled={form.isLoading}
          >
            <Fragment>
              <option value="">Ekkert valið</option>
              {buildingTypes.map(([slug, label]) => {
                return <option value={slug}>{label}</option>;
              })}
            </Fragment>
          </Select>
        </div>
      </div>
      <div class="mb-4 grid gap-2 grid-cols-3">
        <div>
          <label class="text-sm block mb-1">Einingar</label>
          <TextInput
            value={form.data.units}
            onChange={(e) =>
              setForm({
                ...form,
                data: { ...form.data, units: e.target.value },
              })
            }
          />
        </div>
        <div>
          <label class="text-sm block mb-1">Viðbætt</label>
          <TextInput
            value={form.data.area_added}
            onChange={(e) =>
              setForm({
                ...form,
                data: { ...form.data, area_added: e.target.value },
              })
            }
          />
        </div>
        <div>
          <label class="text-sm block mb-1">Niðurrif</label>
          <TextInput
            value={form.data.area_subtracted}
            onChange={(e) =>
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

import { useField, useForm } from "@shopify/react-form";
import {
  BuildingTypeEnum,
  EnumListResponse,
  Permit,
  PermitTypeEnum,
  useGetEnums,
  useGetPermit,
  useUpdatePermit,
} from "../api/types";

import { NumberInput, Primary, Select } from "../forms/widgets";

function Form({
  minuteId,
  permit,
  enums,
}: {
  minuteId: number;
  permit: Permit;
  enums: EnumListResponse;
}) {
  const { mutateAsync } = useUpdatePermit();

  const building_types = enums.building_types as [BuildingTypeEnum, string][];
  const permit_types = enums.permit_types as [PermitTypeEnum, string][];

  const { fields, submitting, submit, dirty } = useForm({
    fields: {
      units: useField<number | null>(permit.units),
      area_added: useField<number | null>(permit.area_added),
      area_subtracted: useField<number | null>(permit.area_subtracted),
      permit_type: useField<PermitTypeEnum | null>(permit.permit_type),
      building_type: useField<BuildingTypeEnum | null>(permit.building_type),
    },
    async onSubmit(form) {
      await mutateAsync({
        minuteId,
        data: {
          units: form.units,
          area_added: form.area_added,
          area_subtracted: form.area_subtracted,
          permit_type: form.permit_type,
          building_type: form.building_type,
        },
      });
      return { status: "success" };
    },
  });
  const created = !!permit.created;

  return (
    <form onSubmit={submit} className="mt-8">
      <div className="mb-3 grid gap-2 grid-cols-2 align-middle">
        <label className="block mb-1">Tegund leyfis</label>
        <Select
          value={fields.permit_type.value || ""}
          onChange={({ target }) =>
            fields.permit_type.onChange(
              (target.value as PermitTypeEnum) || null
            )
          }
        >
          <option value="">Ekkert valið</option>
          {permit_types.map(([slug, label]) => (
            <option key={slug} value={slug}>
              {label}
            </option>
          ))}
        </Select>
        <label className="block mb-1">Tegund byggingar</label>
        <Select
          value={fields.building_type.value || ""}
          onChange={({ target }) =>
            fields.building_type.onChange(target.value as BuildingTypeEnum)
          }
        >
          <option value="">Ekkert valið</option>
          {building_types.map(([slug, label]) => (
            <option key={slug} value={slug}>
              {label}
            </option>
          ))}
        </Select>
        <label className="block mb-1">Einingar</label>
        <NumberInput
          min={0}
          value={fields.units.value}
          onChange={({ target }) => fields.units.onChange(target.valueAsNumber)}
        />
        <label className="block mb-1">Viðbætt</label>
        <NumberInput
          step="0.1"
          min={0}
          value={fields.area_added.value}
          onChange={({ target }) =>
            fields.area_added.onChange(target.valueAsNumber)
          }
        />
        <label className="block mb-1">Niðurrif</label>
        <NumberInput
          step="0.1"
          min={0}
          value={fields.area_subtracted.value}
          onChange={({ target }) =>
            fields.area_subtracted.onChange(target.valueAsNumber)
          }
        />
      </div>
      <div className="flex items-baseline mb-2">
        <div className="flex-grow text-right text-gray-500 pr-4">
          {(created && "Vistað") || "Ekkert leyfi vistað"}
        </div>
        <div className="">
          <Primary type="submit" disabled={submitting || !dirty}>
            {(!created && "Vista") || "Uppfæra"}
          </Primary>
        </div>
      </div>
    </form>
  );
}

export const PermitForm = ({ minuteId }: { minuteId: string }) => {
  const { data } = useGetPermit(parseInt(minuteId, 10));
  const { data: enums } = useGetEnums();

  if (!data || !enums) {
    return <div>Hleð ...</div>;
  }

  return <Form permit={data} enums={enums} minuteId={parseInt(minuteId, 10)} />;
};

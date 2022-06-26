import { notEmptyString, useField, useForm } from "@shopify/react-form";
import { AxiosError } from "axios";
import { useState } from "react";
import { useRecoverPassword } from "../api/types";
import { Primary, TextInput } from "./widgets";

export const PasswordRecoveryForm = ({ setScreen, emailDefaultValue }) => {
  const { mutateAsync } = useRecoverPassword();
  const [message, setMessage] = useState("");
  const { fields, submit, submitting, dirty } = useForm({
    fields: {
      email: useField({
        value: emailDefaultValue || "",
        validates: notEmptyString("Netfang vantar"),
      }),
    },
    async onSubmit(form) {
      try {
        const response = await mutateAsync({ ...form });
        setMessage(response.msg);
      } catch (error) {
        if (error instanceof AxiosError) {
          setMessage(
            error.response.status === 404
              ? "Netfang fannst ekki"
              : "Villa á vefþjóni"
          );
        } else {
          throw error;
        }
      }
      return { status: "success" };
    },
  });

  return (
    <div>
      <h1 className="text-center text-2xl">Sækja um nýtt lykilorð</h1>
      <div className="pt-6 pb-2 my-2">
        <form onSubmit={submit}>
          {message && (
            <div className="mb-8 shadow-planitor-green rounded-lg px-3 py-2 font-medium text-center text-planitor-green bg-planitor-green/30">
              {message}
            </div>
          )}
          <div className="flex gap-3 items-center">
            <TextInput
              value={fields.email.value}
              onChange={fields.email.onChange}
              className="w-full"
            />
            <Primary type="submit" disabled={submitting || !dirty}>
              Senda
            </Primary>
          </div>
        </form>
        <div className="mt-4 md:mt-0">
          <button
            onClick={(event) => {
              event.stopPropagation();
              setScreen(["login", fields.email.value]);
            }}
            className="no-underline"
          >
            Til baka
          </button>
        </div>
      </div>
    </div>
  );
};

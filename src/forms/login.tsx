import { notEmptyString, useField, useForm } from "@shopify/react-form";
import { AxiosError } from "axios";
import { useLoginAccessToken } from "../api/types";
import { TextInput, PasswordInput } from "./widgets";

export function LoginForm({
  onSuccess,
  setScreen,
}: {
  onSuccess: () => void;
  setScreen: any;
}) {
  const { mutateAsync } = useLoginAccessToken();
  const { fields, submit, submitting, submitErrors, dirty } = useForm({
    fields: {
      email: useField({
        value: "",
        validates: notEmptyString("Netfang vantar"),
      }),
      password: useField({
        value: "",
        validates: notEmptyString("Lykilorð vantar"),
      }),
    },
    makeCleanAfterSubmit: true,
    async onSubmit(form) {
      try {
        const response = await mutateAsync({
          data: { username: form.email, password: form.password },
        });
        localStorage.setItem("token", response.access_token);
      } catch (error) {
        if (error instanceof AxiosError) {
          return {
            status: "fail",
            errors: [{ message: error.response.data.detail }],
          };
        }
        return {
          status: "fail",
          errors: [{ message: "Innskráning tókst ekki" }],
        };
      }
      onSuccess();
      return { status: "success" };
    },
  });
  return (
    <div>
      <h1 className="text-2xl">Innskráning</h1>
      <div className="pt-6 pb-2 my-2">
        <form onSubmit={submit}>
          {submitErrors
            .filter((error) => !error.field)
            .map((error) => (
              <div key={String(error)} className="mb-4 text-red-700 font-bold">
                {error.message}
              </div>
            ))}
          <div className="mb-4">
            <label className="block text-sm mb-2">
              <div className="mb-2">Netfang</div>
              <TextInput
                onChange={fields.email.onChange}
                value={fields.email.value}
                isInvalid={!!fields.email.error}
              />
            </label>
            {fields.email.error && (
              <div className="text-red-700 text-sm my-2">
                {fields.email.error}
              </div>
            )}
          </div>
          <div className="mb-6">
            <label className="block text-sm mb-2">
              <div className="mb-2">Lykilorð</div>
              <PasswordInput
                onChange={fields.password.onChange}
                value={fields.password.value}
                isInvalid={!!fields.password.error}
              />
            </label>
            {fields.password.error && (
              <div className="text-red-700 text-sm my-2">
                {fields.password.error}
              </div>
            )}
          </div>
          <div className="block sm:flex items-center justify-between">
            <div>
              <button
                className="btn-primary"
                type="submit"
                disabled={submitting || !dirty}
              >
                Innskrá
              </button>
            </div>
            <div className="mt-4 sm:mt-0">
              <button
                onClick={(event) => {
                  event.stopPropagation();
                  setScreen(["password-recovery", fields.email.value]);
                }}
                className="no-underline"
              >
                Gleymt lykilorð?
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

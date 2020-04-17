import { h } from "preact";
import { useState } from "preact/hooks";
import { api } from "../api";

const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

export const PasswordRecoveryForm = ({ setScreen, emailDefaultValue }) => {
  const [form, setForm] = useState({
    isLoading: false,
    isSuccess: false,
    error: null,
  });

  const [email, setEmail] = useState({
    value: emailDefaultValue,
    isDirty: false,
  });

  const onSubmit = (event) => {
    event.preventDefault();
    setForm({ isLoading: true, isSuccess: false, error: null });
    api
      .passwordRecovery(email.value)
      .then((response) => {
        console.log("success", response.data);
        setForm({ isLoading: false, error: null, isSuccess: true });
      })
      .catch(function (error) {
        // remove dirty from email, meant for highlighting invalid fields until user edits
        setEmail((prevState) => ({
          ...prevState,
          isDirty: false,
        }));
        let errorMessage =
          error.response.data.detail || "Óþekkt villa á vefþjóni";
        setForm({
          isLoading: false,
          isSuccess: false,
          error: errorMessage,
        });
      });
  };

  const onEmailChange = (event) => {
    const { value } = event.target;
    setEmail({ value: value, isDirty: true });
  };

  return (
    <div>
      <h1 class="text-center text-2xl">Sækja um nýtt lykilorð</h1>
      <div class="pt-6 pb-2 my-2">
        <form onSubmit={onSubmit}>
          {form.error && (
            <div class="mb-4 text-red-700 font-bold">{form.error}</div>
          )}
          {form.isSuccess && (
            <div class="mb-4 text-green-600 font-bold">
              Tölvupóstur með leiðbeiningum var sendur á {email.value}
            </div>
          )}
          <div class="mb-4">
            <label class="block text-sm font-bold mb-2" for="email">
              Netfang
            </label>
            <input
              class="shadow appearance-none border rounded w-full py-2 px-3"
              name="email"
              type="text"
              disabled={form.isLoading || form.isSuccess}
              value={email.value}
              onInput={onEmailChange}
            />
          </div>
          <div class="block md:flex items-center justify-between">
            <div>
              <button
                class="btn-primary"
                type="submit"
                disabled={form.isLoading || form.isSuccess}
              >
                Senda
              </button>
            </div>

            <div class="mt-4 md:mt-0">
              <button
                onClick={(event) => {
                  event.stopPropagation();
                  setScreen(["login", email.value]);
                }}
                class="no-underline"
              >
                Til baka
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

import { h } from "preact";
import { useState } from "preact/hooks";
import { api } from "./api";

const getLocalToken = () => localStorage.getItem("token");
const saveLocalToken = (token) => localStorage.setItem("token", token);
const removeLocalToken = () => localStorage.removeItem("token");

const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

export const SignupForm = () => {
  const [usernameState, setUsernameState] = useState({
    value: "",
    isDirty: false,
    errors: [],
  });
  const [passwordState, setPasswordState] = useState({
    value: "",
    isDirty: false,
    errors: [],
  });
  const [formState, setFormState] = useState({ isLoading: false, error: null });

  const onSubmit = (event) => {
    event.preventDefault();
    const state = {
      username: usernameState.value,
      password: passwordState.value,
    };

    setFormState({ isLoading: true, error: null });

    api
      .logInGetToken(usernameState.value, passwordState.value)
      .then((response) => {
        console.log("success", response);
      })
      .catch(function (error) {
        // handle error

        // remove dirty from fields, meant for highlighting invalid fields until user edits
        [setUsernameState, setPasswordState].forEach((setState) => {
          setState((prevState) => ({
            ...prevState,
            errors: [],
            isDirty: false,
          }));
        });

        const errors = error.response.data.detail;

        let formError = null;

        if (typeof errors == "string") {
          formError = errors;
        }

        if (Array.isArray(errors)) {
          errors.forEach((error) => {
            const { loc, msg, type } = error;
            const msgTranslation = { "value_error.missing": true }[type];
            if (msgTranslation === undefined) return;
            const fieldName = loc[loc.length - 1];
            const setState = {
              username: setUsernameState,
              password: setPasswordState,
            }[fieldName];
            if (setState === undefined) return;
            setState((prevState) => ({
              ...prevState,
              errors: [msgTranslation],
            }));
          });
        }

        setFormState({ isLoading: false, error: formError });
      });
  };

  const onUsernameChange = (event) => {
    const { value } = event.target;
    setUsernameState((prevState) => ({
      ...prevState,
      value: value,
      isDirty: true,
    }));
  };

  const onPasswordChange = (event) => {
    const { value } = event.target;
    setPasswordState((prevState) => ({
      ...prevState,
      value: value,
      isDirty: true,
    }));
  };

  return (
    <div>
      <h1 class="text-center text-2xl text-green-dark">Innskráning</h1>
      <div class="pt-6 pb-2 my-2">
        <form onSubmit={onSubmit}>
          {formState.error && (
            <div class="mb-4 text-red-700 font-bold">{formState.error}</div>
          )}
          <div class="mb-4">
            <label class="block text-sm font-bold mb-2" for="username">
              Netfang
            </label>
            <input
              class={classNames([
                "shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker",
                (!usernameState.isDirty &&
                  !!usernameState.errors.length &&
                  "error") ||
                  "",
              ])}
              name="username"
              type="text"
              disabled={formState.isLoading}
              value={usernameState.value}
              onInput={onUsernameChange}
            />
            {usernameState.errors.map((error) => {
              return <div class="text-red-700 text-sm my-2">{error}</div>;
            })}
          </div>
          <div class="mb-6">
            <label class="block text-sm font-bold mb-2" for="password">
              Lykilorð
            </label>
            <input
              class={classNames([
                "shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker mb-3",
                (!passwordState.isDirty &&
                  !!passwordState.errors.length &&
                  "error") ||
                  "",
              ])}
              name="password"
              type="password"
              disabled={formState.isLoading}
              value={passwordState.value}
              onInput={onPasswordChange}
            />
            {passwordState.errors.map((error) => {
              return <div class="text-red-700 text-sm my-2">{error}</div>;
            })}
          </div>
          <div class="block md:flex items-center justify-between">
            <div>
              <button
                class="btn-primary"
                type="submit"
                disabled={formState.isLoading}
              >
                Innskrá
              </button>
            </div>

            <div class="mt-4 md:mt-0">
              <a href="#" class="text-green no-underline">
                Gleymt lykilorð?
              </a>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

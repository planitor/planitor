import { h } from "preact";
import { useState } from "preact/hooks";
import { api } from "../api";

const getLocalToken = () => localStorage.getItem("token");
const saveLocalToken = (token) => localStorage.setItem("token", token);
const removeLocalToken = () => localStorage.removeItem("token");

const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

export const LoginForm = (props) => {
  const { success, setScreen } = props;
  const [username, setUsername] = useState({
    value: "",
    isDirty: false,
    errors: [],
  });
  const [password, setPassword] = useState({
    value: "",
    isDirty: false,
    errors: [],
  });
  const [form, setForm] = useState({ isLoading: false, error: null });

  const onSubmit = (event) => {
    event.preventDefault();
    setForm({ isLoading: true, error: null });
    api
      .logInGetToken(username.value, password.value)
      .then((response) => {
        saveLocalToken(response.data.access_token);
        success();
      })
      .catch(function (error) {
        // handle error

        // remove dirty from fields, meant for highlighting invalid fields until user edits
        [setUsername, setPassword].forEach((setState) => {
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
            // The API has types of errors (from Pydantic: https://pydantic-docs.helpmanual.io/usage/models/#error-handling)
            const msgTranslation = { "value_error.missing": true }[type];
            if (msgTranslation === undefined) return;
            const fieldName = loc[loc.length - 1];
            const setState = {
              username: setUsername,
              password: setPassword,
            }[fieldName];
            if (setState === undefined) return;
            setState((prevState) => ({
              ...prevState,
              errors: [msgTranslation],
            }));
          });
        }

        setForm({ isLoading: false, error: formError });
      });
  };

  const onUsernameChange = (event) => {
    const { value } = event.target;
    setUsername((prevState) => ({
      ...prevState,
      value: value,
      isDirty: true,
    }));
  };

  const onPasswordChange = (event) => {
    const { value } = event.target;
    setPassword((prevState) => ({
      ...prevState,
      value: value,
      isDirty: true,
    }));
  };

  return (
    <div>
      <h1 class="text-center text-2xl">Innskráning</h1>
      <div class="pt-6 pb-2 my-2">
        <form onSubmit={onSubmit}>
          {form.error && (
            <div class="mb-4 text-red-700 font-bold">{form.error}</div>
          )}
          <div class="mb-4">
            <label class="block text-sm font-bold mb-2" for="username">
              Netfang
            </label>
            <input
              class={classNames([
                "shadow appearance-none border rounded w-full py-2 px-3",
                (!username.isDirty && !!username.errors.length && "error") ||
                  "",
              ])}
              name="username"
              type="text"
              disabled={form.isLoading}
              value={username.value}
              onInput={onUsernameChange}
            />
            {username.errors.map((error) => {
              return <div class="text-red-700 text-sm my-2">{error}</div>;
            })}
          </div>
          <div class="mb-6">
            <label class="block text-sm font-bold mb-2" for="password">
              Lykilorð
            </label>
            <input
              class={classNames([
                "shadow appearance-none border rounded w-full py-2 px-3 mb-3",
                (!password.isDirty && !!password.errors.length && "error") ||
                  "",
              ])}
              name="password"
              type="password"
              disabled={form.isLoading}
              value={password.value}
              onInput={onPasswordChange}
            />
            {password.errors.map((error) => {
              return <div class="text-red-700 text-sm my-2">{error}</div>;
            })}
          </div>
          <div class="block sm:flex items-center justify-between">
            <div>
              <button
                class="btn-primary"
                type="submit"
                disabled={form.isLoading}
              >
                Innskrá
              </button>
            </div>
            <div class="mt-4 sm:mt-0">
              <button
                onClick={(event) => {
                  event.stopPropagation();
                  setScreen(["password-recovery", username.value]);
                }}
                class="no-underline"
              >
                Gleymt lykilorð?
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
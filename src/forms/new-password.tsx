import { useState } from "react";
import { resetPassword } from "../api/client";
import { PasswordInput } from "./widgets";

const saveLocalToken = (token) => localStorage.setItem("token", token);

export const NewPasswordForm = ({ token }) => {
  const [form, setForm] = useState({
    isSuccess: false,
    isLoading: false,
    error: null,
  });
  const [password, setPassword] = useState("");

  const onChange = (event) => {
    setPassword(event.target.value);
  };

  const onSubmit = (event) => {
    event.preventDefault();
    setForm({ isLoading: true, isSuccess: false, error: null });
    resetPassword(password, token)
      .then((response) => {
        saveLocalToken(response.data.access_token);
        setForm({ isLoading: false, error: null, isSuccess: true });
      })
      .catch(function (error) {
        // remove dirty, meant for highlighting invalid fields until user edits
        let errorMessage =
          error.response.data.detail || "Óþekkt villa á vefþjóni";
        setForm({ isLoading: false, isSuccess: false, error: errorMessage });
      });
  };

  return (
    <div>
      <h1 className="text-center text-2xl">Nýtt lykilorð</h1>
      <div className="py-2 my-2"></div>
      <form onSubmit={onSubmit}>
        {form.error && (
          <div className="mb-4 text-red-700 font-bold">{form.error}</div>
        )}
        {form.isSuccess && (
          <div className="mb-4 text-green-600 font-bold">
            Lykilorðið hefur verið uppfært.
          </div>
        )}
        <div className="mb-4">
          <PasswordInput
            name="password"
            type="password"
            disabled={form.isLoading || form.isSuccess}
            value={password.value}
            onInput={onChange}
          />
        </div>
        <div className="block md:flex items-center justify-between">
          <div>
            <button
              className="btn-primary"
              type="submit"
              disabled={form.isLoading || form.isSuccess}
            >
              Vista
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

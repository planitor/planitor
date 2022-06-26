import { useState } from "react";
import { useResetPassword } from "../api/types";
import { PasswordInput } from "./widgets";

const saveLocalToken = (token) => localStorage.setItem("token", token);

export const NewPasswordForm = ({ token }) => {
  const { mutateAsync } = useResetPassword();
  const [form, setForm] = useState({
    isSuccess: false,
    isLoading: false,
    error: null,
  });
  const [password, setPassword] = useState("");

  const onChange = (password: string) => {
    setPassword(password);
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setForm({ isLoading: true, isSuccess: false, error: null });
    const data = await mutateAsync({
      data: { new_password: password, token },
    }).catch(function (error) {
      // remove dirty, meant for highlighting invalid fields until user edits
      let errorMessage =
        error.response.data.detail || "Óþekkt villa á vefþjóni";
      setForm({ isLoading: false, isSuccess: false, error: errorMessage });
    });
    saveLocalToken(data);
    setForm({ isLoading: false, error: null, isSuccess: true });
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
            disabled={form.isLoading || form.isSuccess}
            value={password}
            onChange={({ target }) => {
              onChange(target.value);
            }}
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

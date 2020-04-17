import { h } from "preact";
import { useState } from "preact/hooks";
import { LoginForm } from "./forms/login";
import { PasswordRecoveryForm } from "./forms/password-recovery";

export const Login = () => {
  const [[screen, emailDefaultValue], setScreen] = useState(["login", ""]);
  const Form = { login: LoginForm, "password-recovery": PasswordRecoveryForm }[
    screen
  ];
  console.log(Form, emailDefaultValue);
  return (
    <div>
      <Form setScreen={setScreen} emailDefaultValue={emailDefaultValue} />
    </div>
  );
};

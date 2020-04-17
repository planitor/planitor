import { h } from "preact";
import { useState } from "preact/hooks";
import { LoginForm } from "./forms/login";
import { NewPasswordForm } from "./forms/new-password";
import { PasswordRecoveryForm } from "./forms/password-recovery";

export const NewPassword = NewPasswordForm;

export const Login = (success) => {
  const [[screen, emailDefaultValue], setScreen] = useState(["login", ""]);
  const Form = { login: LoginForm, "password-recovery": PasswordRecoveryForm }[
    screen
  ];
  console.log(Form, emailDefaultValue);
  return (
    <div>
      <Form
        setScreen={setScreen}
        emailDefaultValue={emailDefaultValue}
        success={success}
      />
    </div>
  );
};

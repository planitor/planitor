import { h } from "preact";
import { useState } from "preact/hooks";
import { LoginForm } from "./forms/login";
import { NewPasswordForm } from "./forms/new-password";
import { PasswordRecoveryForm } from "./forms/password-recovery";

export const NewPassword = NewPasswordForm;

export const Login = (props) => {
  const { onSuccess } = props;
  const [[screen, emailDefaultValue], setScreen] = useState(["login", ""]);
  const Form = { login: LoginForm, "password-recovery": PasswordRecoveryForm }[
    screen
  ];
  return (
    <div>
      <Form
        setScreen={setScreen}
        emailDefaultValue={emailDefaultValue}
        onSuccess={onSuccess}
      />
    </div>
  );
};

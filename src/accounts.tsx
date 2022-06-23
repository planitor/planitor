import { useState } from 'react';
import { LoginForm } from "./forms/login";
import { PasswordRecoveryForm } from "./forms/password-recovery";

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

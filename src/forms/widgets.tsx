// const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

import classNames from "classnames";
import { FC, PropsWithChildren } from "react";

type InputProps = Pick<
  React.HTMLProps<HTMLInputElement>,
  "value" | "type" | "max" | "min" | "step" | "disabled"
> & {
  isInvalid?: boolean;
  isDirty?: boolean;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
};

const Input = ({
  value,
  onChange,
  isDirty,
  isInvalid,
  type,
  ...props
}: InputProps) => {
  return (
    <div className="text-sm lg-text-base">
      <input
        type={type}
        onChange={onChange}
        value={value || ""}
        className={classNames(
          "block w-full rounded-md border-1 border-gray-400",
          "focus:ring-powder-default focus:ring-2"
        )}
        {...props}
      />
    </div>
  );
};

export const TextInput: FC<Omit<InputProps, "type">> = (props) => {
  return <Input {...props} type="text" />;
};

export const NumberInput: FC<
  InputProps & Pick<React.HTMLProps<HTMLInputElement>, "max" | "min" | "step">
> = (props) => {
  return (
    <Input
      {...props}
      max={props.max || undefined}
      min={props.min || 0}
      step={props.step || 1}
      type="number"
    />
  );
};

export const PasswordInput: FC<Omit<InputProps, "type">> = (props) => {
  return <Input {...props} type="password" />;
};

export const Select: FC<
  PropsWithChildren<React.HTMLProps<HTMLSelectElement>>
> = ({ value, onChange, disabled = false, children }) => {
  return (
    <div className="text-sm lg:text-base">
      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={classNames(
          "block w-full rounded-md border-1 border-gray-400",
          "focus:ring-powder-default focus:ring-2"
        )}
      >
        {children}
      </select>
    </div>
  );
};

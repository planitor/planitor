// const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

import classNames from "classnames";
import { FC, PropsWithChildren } from "react";

type InputProps = Pick<
  React.HTMLProps<HTMLInputElement>,
  "value" | "type" | "max" | "min" | "step" | "disabled" | "className"
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
  className,
  ...props
}: InputProps) => {
  return (
    <input
      type={type}
      onChange={onChange}
      value={value || ""}
      className={classNames(
        className,
        "block w-full rounded-md border-1 border-gray-400 font-normal",
        "focus:ring-powder-default focus:ring-2"
      )}
      {...props}
    />
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
  PropsWithChildren<React.SelectHTMLAttributes<HTMLSelectElement>>
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

export const Primary: FC<
  PropsWithChildren<React.ButtonHTMLAttributes<HTMLButtonElement>>
> = ({ className, children, ...props }) => (
  <button
    {...props}
    className={classNames(
      className,
      "transition-all",
      "focus:ring-powder-default focus:ring",
      "text-white font-semibold rounded-md px-3 py-2",
      "bg-planitor-blue enabled:hover:bg-planitor-darkBlue border",
      "border-planitor-blue enabled:hover:border-planitor-darkBlue",
      "disabled:opacity-60 disabled:hover:bg-planitor-blue disabled:cursor-default"
    )}
  >
    {children}
  </button>
);

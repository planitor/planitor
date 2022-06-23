// const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

import { FC, PropsWithChildren } from "react";

const inputStyling =
  "mt-1 block w-full rounded-md bg-black/10 border-transparent focus:border-gray-500 focus:bg-white focus:ring-0";

type InputProps = Pick<
  React.HTMLProps<HTMLInputElement>,
  "value" | "type" | "max" | "min" | "step" | "onInput" | "disabled"
> & {
  isInvalid?: boolean;
  isDirty?: boolean;
};

const Input = ({
  value,
  onInput,
  isDirty,
  isInvalid,
  type,
  ...props
}: InputProps) => {
  return (
    <div className="text-sm lg-text-base">
      <input
        type={type}
        onInput={onInput}
        value={value || ""}
        className={inputStyling}
        {...props}
      />
    </div>
  );
};

export const TextInput: FC<InputProps> = (props) => {
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

export const PasswordInput: FC<InputProps> = (props) => {
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
        className="block w-full mt-1 rounded-md bg-opacity-10 border-transparent focus:border-gray-500 focus:bg-white focus:ring-0"
      >
        {children}
      </select>
    </div>
  );
};

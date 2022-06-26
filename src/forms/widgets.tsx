// const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

import classNames from "classnames";
import { FC, PropsWithChildren } from "react";

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
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
        "block w-full rounded-md border-1 font-normal",
        "focus:ring-powder-default focus:ring-2",
        isInvalid ? "border-planitor-red" : "border-gray-400"
      )}
      {...props}
    />
  );
};

export const TextInput: FC<Omit<InputProps, "type">> = (props) => (
  <Input {...props} type="text" />
);

export const NumberInput: FC<Omit<InputProps, "type">> = (props) => (
  <Input {...props} type="number" />
);

export const PasswordInput: FC<Omit<InputProps, "type">> = (props) => (
  <Input {...props} type="password" />
);

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

export const FollowButton: FC<
  PropsWithChildren<
    React.ButtonHTMLAttributes<HTMLButtonElement> & {
      loading: boolean;
      hover: boolean;
      setHover: (value: boolean) => void;
      following: boolean;
      defaultLabel?: string;
    }
  >
> = ({
  className,
  children,
  loading,
  onClick,
  hover,
  setHover,
  following,
  defaultLabel,
  ...props
}) => (
  <button
    className={classNames(
      "sm:inline block mx-auto",
      "focus:ring-powder-default focus:ring",
      "text-white font-semibold rounded-md px-3 py-2",
      "enabled:hover:border-planitor-darkBlue",
      "disabled:opacity-60 disabled:cursor-default",
      {
        "bg-planitor-blue enabled:hover:bg-planitor-darkBlue text-white disabled:hover:bg-planitor-blue":
          following,
        "text-planitor-blue bg-powder-dark enabled:hover:ring-2 enabled:hover:bg-powder-default":
          !following,
      }
    )}
    onClick={onClick}
    disabled={loading}
    onMouseOver={(event) => {
      setHover(true);
    }}
    onMouseOut={(event) => {
      setHover(false);
    }}
    {...props}
  >
    {(() => {
      if (hover) {
        return following ? "Afvakta" : defaultLabel || "Vakta";
      } else {
        return following ? "Vaktað" : defaultLabel || "Vakta";
      }
    })()}
  </button>
);

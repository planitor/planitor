import { h, render } from "preact";

// const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

const inputStyling =
  "mt-1 block w-full rounded-md bg-black bg-opacity-10 border-transparent focus:border-gray-500 focus:bg-white focus:ring-0";

const Input = ({
  value,
  onInput,
  isDisabled,
  isDirty,
  isInvalid,
  inputProps,
  type,
  ...props
}) => {
  return (
    <div class="text-sm lg-text-base">
      <input
        type={type}
        onInput={onInput}
        value={value}
        disabled={isDisabled}
        class={inputStyling}
        {...props}
      />
    </div>
  );
};

export const TextInput = (props) => {
  return <Input {...props} type="text" />;
};

export const NumberInput = (props) => {
  return (
    <Input
      {...props}
      max={props.max || null}
      min={props.min || 0}
      step={props.step || 1}
      type="number"
    />
  );
};

export const PasswordInput = (props) => {
  return <Input {...props} type="password" />;
};

export const Select = ({ value, onChange, isDisabled, children }) => {
  return (
    <div class="text-sm lg:text-base">
      <select
        value={value}
        onChange={onChange}
        disabled={isDisabled}
        class="block w-full mt-1 rounded-md bg-black bg-opacity-10 border-transparent focus:border-gray-500 focus:bg-white focus:ring-0"
      >
        {children}
      </select>
    </div>
  );
};

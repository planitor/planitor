import { h, render } from "preact";

const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

const Input = ({ value, onInput, isDisabled, isDirty, isInvalid, type }) => {
  return (
    <div class="text-sm lg-text-base">
      <input
        type={type}
        class={classNames([
          "mt-0 block w-full px-0.5 border-0 border-b-2 border-gray-200 focus:ring-0 focus:border-black",
          (!isDirty && isInvalid && "border-red-700") || null,
        ])}
        onInput={onInput}
        value={value}
        disabled={isDisabled}
        class="mt-0 block w-full px-0.5 border-0 border-b-2 border-gray-200 focus:ring-0 focus:border-black bg-transparent"
      />
    </div>
  );
};

export const TextInput = (props) => {
  return <Input {...props} type="text" />;
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
        class="block w-full mt-0 px-0.5 border-0 border-b-2 border-gray-200 focus:ring-0 focus:border-black bg-transparent"
      >
        {children}
      </select>
    </div>
  );
};

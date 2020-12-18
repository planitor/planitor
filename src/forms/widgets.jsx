import { h, render } from "preact";

const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

const Input = ({ value, onInput, isDisabled, isDirty, isInvalid, type }) => {
  return (
    <div class="text-sm lg-text-base">
      <input
        type={type}
        onInput={onInput}
        value={value}
        disabled={isDisabled}
        class="mt-1 block w-full rounded-md bg-black bg-opacity-10 border-transparent focus:border-gray-500 focus:bg-white focus:ring-0"
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
        class="block w-full mt-1 rounded-md bg-black bg-opacity-10 border-transparent focus:border-gray-500 focus:bg-white focus:ring-0"
      >
        {children}
      </select>
    </div>
  );
};

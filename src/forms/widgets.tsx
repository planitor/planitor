import { FunctionComponent, h } from "preact";

// const classNames = (classArr) => classArr.filter((el) => el).join(" "); // filter falsy values

const inputStyling =
  "mt-1 block w-full rounded-md bg-black bg-opacity-10 border-transparent focus:border-gray-500 focus:bg-white focus:ring-0";

type InputProps = Pick<HTMLInputElement, "value" | "type"> & {
  onInput: () => void;
  isInvalid: boolean;
  isDirty: boolean;
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
    <div class="text-sm lg-text-base">
      <input
        type={type}
        onInput={onInput}
        value={value}
        class={inputStyling}
        {...props}
      />
    </div>
  );
};

export const TextInput: FunctionComponent<InputProps> = (props) => {
  return <Input {...props} type="text" />;
};

export const NumberInput: FunctionComponent<
  InputProps & Pick<HTMLInputElement, "max" | "min" | "step">
> = (props) => {
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

export const PasswordInput: FunctionComponent<InputProps> = (props) => {
  return <Input {...props} type="password" />;
};

export const Select: FunctionComponent<{
  value: string;
  onChange: h.JSX.GenericEventHandler<HTMLSelectElement>;
  disabled?: boolean;
}> = ({ value, onChange, disabled = false, children }) => {
  return (
    <div class="text-sm lg:text-base">
      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        class="block w-full mt-1 rounded-md bg-black bg-opacity-10 border-transparent focus:border-gray-500 focus:bg-white focus:ring-0"
      >
        {children}
      </select>
    </div>
  );
};

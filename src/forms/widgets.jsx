import { h, render } from "preact";

export const SelectWidget = ({ value, onChange, isDisabled, children }) => {
  return (
    <div class="inline-block relative text-sm lg:text-base">
      <select
        value={value}
        onChange={onChange}
        disabled={isDisabled}
        class="block appearance-none w-full border border-gray-400 hover:border-gray-500 px-1 lg:px-4 py-1 lg:py-2 pr-8 mr-3 rounded shadow leading-tight focus:outline-none focus:shadow-outline"
      >
        {children}
      </select>
      <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
        <svg class="fill-current h-4 w-4" viewBox="0 0 20 20">
          <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
        </svg>
      </div>
    </div>
  );
};

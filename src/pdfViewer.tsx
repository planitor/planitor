import { h, render } from "preact";
import { useState, useEffect } from "preact/hooks";

export const PDFViewer = ({ pages, title, initialIndex, onClose }) => {
  const [index, setIndex] = useState(initialIndex);
  const [loaded, setLoaded] = useState(true);

  const clickPrevious = () => {
    setIndex((index) => {
      if (index === 0) return index;
      setLoaded(false);
      return index - 1;
    });
  };

  const clickNext = () => {
    setIndex((index) => {
      if (index === pages.length - 1) return index;
      setLoaded(false);
      return index + 1;
    });
  };

  const upHandler = (event) => {
    if (event.keyCode === 37) clickPrevious();
    if (event.keyCode === 39) clickNext();
  };

  useEffect(() => {
    window.addEventListener("keyup", upHandler);
    // cleanup
    return () => {
      window.removeEventListener("keyup", upHandler);
    };
  }, []);

  return (
    <div class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" aria-hidden="true">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        {/* This element is to trick the browser into centering the modal contents. */}
        <span
          class="hidden sm:inline-block sm:align-middle sm:h-screen"
          aria-hidden="true"
        >
          &#8203;
        </span>
        <div
          class="inline-block align-bottom bg-white rounded-lg p-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full sm:p-6 max-h-full"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-headline"
        >
          <div class="block absolute top-0 right-0 pt-4 pr-4">
            <button
              type="button"
              onClick={onClose}
              class="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <span class="sr-only">Loka</span>
              {/* Heroicon name: outline/x */}
              <svg
                class="h-6 w-6"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div class="">
            <h3 class="text-lg font-medium text-gray-900" id="modal-headline">
              {title}
            </h3>
            <div class="mt-2">
              <div
                style="max-height: calc(100vh - 210px)"
                class={`overflow-y-auto ${!loaded && "opacity-30"}`}
              >
                <img
                  src={pages[index]}
                  onLoad={() => {
                    setLoaded(true);
                  }}
                />
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-4 flex justify-between items-center">
            <div class="flex-1">
              <button
                type="button"
                class={`btn ${index === 0 || !loaded ? "btn-disabled" : ""}`}
                onClick={clickPrevious}
              >
                ← Fyrri
              </button>
            </div>
            {!loaded && (
              <div class="flex-1 flex justify-center">
                <svg
                  class="animate-spin -ml-1 mr-3 h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  ></circle>
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              </div>
            )}
            <div class="flex-1 flex justify-end">
              <button
                type="button"
                class={`btn ${
                  index === pages.length - 1 || !loaded ? "btn-disabled" : ""
                }`}
                onClick={clickNext}
              >
                Næsta →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

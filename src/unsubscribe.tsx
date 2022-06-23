import { h, render } from "preact";
import { useState, useEffect } from "preact/hooks";

export const Unsubscribe = () => {
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  useEffect(async () => {
    let response;
    try {
      response = await fetch(String(window.location), { method: "POST" });
    } catch (e) {
      setError(String(e));
    }
    if (response && response.status >= 200 && response.status < 300) {
      setSuccess(true);
    } else {
      setError("Villa kom upp");
      console.error("Error response", response);
    }
  });
  if (success) return <div>Afskráning tókst ☑️</div>;
  if (error) return <div>{error}</div>;
  return <div>Augnablik meðan við afskráum þig…</div>;
};

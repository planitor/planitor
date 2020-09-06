import * as Sentry from "@sentry/browser";
import "lazysizes";

if (!typeof process === "undefined") {
  Sentry.init({
    dsn: "__sentryDsn__",
    release: "__version__" || null,
  });
}

import "./styles.css";
import "./app.jsx";

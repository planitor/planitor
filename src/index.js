import * as Sentry from "@sentry/browser";

if (typeof __sentryDsn__ !== "undefined") {
  Sentry.init({
    dsn: __sentryDsn__,
    release: __version__ || null,
  });
  unhandledException();
}

import "lazysizes";
import "./styles.css";
import "./app.jsx";

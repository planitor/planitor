import * as Sentry from "@sentry/browser";

if (typeof __sentryDsn__ !== "undefined") {
  Sentry.init({
    dsn: __sentryDsn__,
    release: __version__ || null,
  });
  if (document._user) {
    const { email, id } = document._user;
    Sentry.setUser({ email, id });
  }
}

import "lazysizes";
import "./styles.css";
import "./app.jsx";

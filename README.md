# Planitor

Planning + Monitoring = Planitor

A business intelligence service for people in the planning, property, transport
and construction sector in Iceland.

# High level

There are two development servers, for bundling frontend and the backend
respectively.

# Development

You will need Python Poetry, Yarn and Postgres.

```bash
createuser planitor
createdb -O planitor planitor
createdb -O planitor planitor_test
```

Configure .env in the project root

```
DEBUG=true
MAPKIT_PRIVATE_KEY=
SECRET_KEY=
PROJECT_NAME=Planitor
DOMAIN=planitor.io
EMAILS_FROM_EMAIL=planitor@{{DOMAIN}}
EMAILS_RESET_TOKEN_EXPIRE_HOURS=2
EMAILS_FROM_NAME=Planitor
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=
SMTP_PASSWORD=
SENTRY_DSN=
```

Install dependencies

```bash
yarn install
poetry install
```

Run server

```bash
poetry run uvicorn planitor.main:app --host 0.0.0.0 --port 5000 --reload
```

Run frontend

```bash
yarn run watch
```

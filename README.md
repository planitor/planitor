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

Preparing deployment

```bash
NODE_ENV=production yarn run build  # frontend build
poetry export -f requirements.txt > requirements.txt
```

Then commit this to repo and push to GitHub. Render takes over from there.

DB Migrations

```bash
poetry run python migrate.py
```

This will create a test database based upon the declarative SQLAlchemy schema,
then use migra to detect the diff, suggest to run a migration to sync the
databases. It shows the SQL migration code which you can copy-paste to tweak.

Run workers

```bash
poetry run dramatiq --watch planitor --processes 2 --threads 2 planitor.actors
```

Run development bpython shell with db object and all models imported

```bash
poetry run python shell.py
```

## Render.com specs

- `dramatiq` background worker
  - Install: `pip install -r requirements.txt`
  - Command: `dramatiq --processes 1 --threads 4 planitor.actors`
- `planitor` web service
  - Install: `pip install -r requirements.txt && pip install gunicorn`
  - Command: `gunicorn -w 1 -k uvicorn.workers.UvicornWorker planitor.main:app`
  - Domain `www.planitor.io` → `planitor-us.onrender.com`
- `crawl` cron job
  - Install:
    `pip install -r requirements.txt && pip install beautifulsoup4 html5lib scrapy`
  - Command: `scrapy list | xargs -n 1 scrapy crawl`
  - Schedule: `0 * * * *` (every hour)

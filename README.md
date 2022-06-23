# Planitor

Planning + Monitoring = Planitor

A business intelligence service for people in the planning, property, transport
and construction sector in Iceland.

# High level

There are two development servers, for bundling frontend and the backend
respectively.

# Development

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
IMGIX_TOKEN=
```

Install dependencies

```bash
npm install
poetry install
```

Use VS Code devcontainer to start the server

Run frontend on host machine

```bash
npm run start
```

Preparing deployment

```bash
NODE_ENV=production yarn run build  # frontend build
poetry export --without-hashes -f requirements.txt > requirements.txt
poetry export --dev --without-hashes -f requirements.txt > requirements-dev.txt
```

Then commit this to repo and push to GitHub. Render takes over from there.

DB Migrations

```bash
poetry run migrate
```

This will create a test database based upon the declarative SQLAlchemy schema,
then use migra to detect the diff, suggest to run a migration to sync the
databases. It shows the SQL migration code which you can copy-paste to tweak.

Run development bpython shell with db object and all models imported

```bash
poetry run debug
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

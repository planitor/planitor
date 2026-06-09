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
npm install
uv sync
```

Use VS Code devcontainer to start the server. Start the devcontainer by opening
the top level folder in VS Code. You'll get a prompt to build and start in
devcontainer. Open a new shell. It should use Fish. Start a reload webserver on
port 80.

```
uv run uvicorn --reload --reload-dir planitor --host 0.0.0.0 --port 80 planitor.main:app
```

Run frontend on host machine

```bash
npm run start
```

Preparing deployment

```bash
NODE_ENV=production yarn run build  # frontend build
uv lock
uv export --frozen --no-dev --no-hashes --output-file requirements.txt
uv export --frozen --all-groups --no-hashes --output-file requirements-dev.txt
```

Then commit this to repo and push to GitHub. Render takes over from there.

DB Migrations

```bash
uv run python -m scripts.migrate
```

This will create a test database based upon the declarative SQLAlchemy schema,
then use migra to detect the diff, suggest to run a migration to sync the
databases. It shows the SQL migration code which you can copy-paste to tweak.

Run development bpython shell with db object and all models imported

```bash
uv run python -m scripts.shell
```

## Render.com specs

- `dramatiq` background worker
  - Install: `uv sync --frozen --no-dev`
  - Command: `uv run dramatiq --processes 1 --threads 4 planitor.actors`
- `planitor` web service
  - Install: `uv sync --frozen --no-dev`
  - Command: `uv run gunicorn -w 1 -k uvicorn.workers.UvicornWorker planitor.main:app`
  - Domain `www.planitor.io` → `planitor-us.onrender.com`
- `crawl` cron job
  - Install: `uv sync --frozen --no-dev`
  - Command: `uv run sh -c "scrapy list | xargs -n 1 scrapy crawl"`
  - Schedule: `0 * * * *` (every hour)

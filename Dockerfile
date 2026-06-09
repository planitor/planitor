# syntax = docker/dockerfile:1.3
FROM python:3.11

WORKDIR /code

# Install system packages for Fiona python package
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
  && apt-get -y install --no-install-recommends gdal-bin libgdal-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.9.28

COPY pyproject.toml uv.lock /code/

RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

COPY . /code/

ENV PATH="/code/.venv/bin:$PATH"

ENV PLANITOR_UVICORN_WORKERS=3

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1/healthz', timeout=3).read()" || exit 1

CMD uvicorn --proxy-headers --host 0.0.0.0 --port 80 --workers "${PLANITOR_UVICORN_WORKERS}" planitor.main:app

# syntax = docker/dockerfile:1.3
FROM python:3.11

WORKDIR /code

ENV \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=1 \
  PATH="/code/.venv/bin:$PATH"

RUN apt-get update \
  && apt-get install --no-install-recommends -y \
  curl gdal-bin libgdal-dev fish \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN pip install uv==0.9.28

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

RUN chsh -s /usr/bin/fish

COPY ./planitor /code/planitor
COPY ./scrape /code/scrape

# syntax = docker/dockerfile:1.3
# this ^^ line is very important as it enables support for --mount=type=cache
# ref: https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/syntax.md#run---mounttypecache

## --- globals

# the following arguments aredefined via ARG to use later in other base images
# ref: https://github.com/moby/moby/issues/37345
ARG POETRY_HOME="/opt/poetry"
ARG PYSETUP_PATH="/opt/pysetup"


## --- poetry base image
FROM python:3.9

WORKDIR /code

ARG POETRY_HOME
ARG PYSETUP_PATH
# python env
ENV \
  ## - python
  PYTHONUNBUFFERED=1 \
  # prevents python creating .pyc files
  PYTHONDONTWRITEBYTECODE=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  \
  ## - pip
  PIP_NO_CACHE_DIR=1 \
  \
  ## - poetry
  # https://python-poetry.org/docs/configuration/#using-environment-variables
  # make poetry install to this location
  POETRY_HOME=$POETRY_HOME \
  # do not ask any interactive question
  POETRY_NO_INTERACTION=1 \
  # poetry specific cache
  POETRY_CACHE_DIR="/opt/poetry/.cache" \
  \
  ## - paths
  # this is where our requirements will live
  PYSETUP_PATH=$PYSETUP_PATH
# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$PATH"

# install curl and essentials
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
  # deps for installing poetry
  curl gdal-bin libgdal-dev fish \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
# install poetry
# by default it respects $POETRY_HOME
RUN pip install poetry

COPY pyproject.toml poetry.lock ./

# install runtime deps
# it also uses poetry caching, thanks @cbrochtrup
# ref: https://github.com/python-poetry/poetry/issues/3374#issuecomment-857878275
RUN --mount=type=cache,target=$POETRY_CACHE_DIR/cache \
  --mount=type=cache,target=$POETRY_CACHE_DIR/artifacts \
  poetry install

ARG PYSETUP_PATH
ENV PATH="$PYSETUP_PATH/.venv/bin:$PATH"

RUN chsh -s /usr/bin/fish

COPY ./planitor /code/planitor
COPY ./scrape /code/scrape

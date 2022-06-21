FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9 as requirements-stage

WORKDIR /tmp
RUN pip install poetry

# Install system packages for Fiona python package
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
  && apt-get -y install --no-install-recommends gdal-bin libgdal-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# Install system packages for Fiona python package
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
  && apt-get -y install --no-install-recommends fish \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN chsh -s /usr/bin/fish

WORKDIR /code
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./planitor /code/planitor
COPY ./scrape /code/scrape
SHELL ["fish", "--command"]
CMD ["uvicorn", "planitor.main:app", "--host", "0.0.0.0", "--port", "80"]

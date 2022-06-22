FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /code

RUN pip install poetry

# Install system packages for Fiona python package
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
  && apt-get -y install --no-install-recommends fish \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY ./pyproject.toml ./poetry.lock* /code/

RUN chsh -s /usr/bin/fish

ENV POETRY_VIRTUALENVS_CREATE=false\
  POETRY_NO_INTERACTION=1

RUN poetry env use system
RUN poetry install

COPY ./planitor /code/planitor
COPY ./scrape /code/scrape

CMD ["uvicorn", "--reload", "--host", "0.0.0.0", "--port", "80", "planitor.main:app"]

FROM python:3.9

WORKDIR /code

# Install system packages for Fiona python package
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
  && apt-get -y install --no-install-recommends gdal-bin libgdal-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install uvicorn gunicorn

COPY . /code/

CMD ["uvicorn", "--proxy-headers", "--host", "0.0.0.0", "--port", "80", "planitor.main:app"]

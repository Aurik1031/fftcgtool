FROM python:3.6-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR "/app"

RUN set -ex; \
    pip3 install pipenv;

COPY Pipfile Pipfile.lock ./

RUN set -ex; \
    \
    # install build prerequisites
    apk add --no-cache \
      build-base \
      jpeg-dev \
      zlib-dev \
    ; \
    pipenv sync; \
    # remove build prerequisites
    apk del --no-cache build-base;

COPY . .

ENTRYPOINT ["pipenv", "run", "./main.py"]

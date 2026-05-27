FROM python:3.14-alpine


RUN apk add --no-cache \
    build-base \
    libffi-dev \
    git \
    curl \
    bash

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /workspaces

CMD ["sleep", "infinity"]
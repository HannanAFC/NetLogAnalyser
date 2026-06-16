FROM python:3.14-alpine


RUN apk add --no-cache \
    build-base \
    libffi-dev \
    git \
    curl \
    bash

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /workspaces

CMD ["sleep", "infinity"]
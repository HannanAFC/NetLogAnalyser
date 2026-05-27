FROM node:25-alpine

RUN apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    build-base \
    libffi-dev \
    git \
    curl \
    bash

RUN npm install -g pnpm

RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /workspaces

CMD ["sleep", "infinity"]
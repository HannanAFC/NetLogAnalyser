FROM node:25-alpine

WORKDIR /app

RUN npm install -g pnpm
RUN apk add curl

COPY package.json pnpm-lock.yaml ./
RUN pnpm install

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
#!/bin/sh
set -eu

envsubst '${BACKEND_PORT}' \
  < /usr/share/nginx/html/config.js.template \
  > /usr/share/nginx/html/config.js

envsubst '${FRONTEND_PORT}' \
  < /etc/nginx/templates/nginx.selfhost.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
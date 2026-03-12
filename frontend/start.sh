#!/bin/sh

PORT=${PORT:-80}

sed -i "s/listen 80/listen $PORT/g" /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"

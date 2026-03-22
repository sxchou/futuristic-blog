#!/bin/sh

PORT=${PORT:-80}

sed -i "s/listen 80/listen $PORT/g" /etc/nginx/conf.d/default.conf

echo "Starting nginx on port $PORT..."

exec nginx -g "daemon off;"

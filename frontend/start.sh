#!/bin/sh

PORT=${PORT:-80}
BACKEND_URL=${BACKEND_URL:-"http://backend.railway.internal:8000"}

sed -i "s/listen 80/listen $PORT/g" /etc/nginx/conf.d/default.conf
sed -i "s|{{BACKEND_URL}}|$BACKEND_URL|g" /etc/nginx/conf.d/default.conf

echo "Starting nginx on port $PORT..."
echo "Backend URL: $BACKEND_URL"

exec nginx -g "daemon off;"

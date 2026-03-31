#!/bin/sh
set -e

echo "========================================"
echo "Starting application..."
echo "PORT environment variable: '${PORT}'"
echo "RAILWAY_ENVIRONMENT: '${RAILWAY_ENVIRONMENT}'"

if [ -z "$PORT" ]; then
    echo "WARNING: PORT is not set, using default 8000"
    PORT=8000
fi

echo "Will listen on port: ${PORT}"
echo "========================================"

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info 2>&1

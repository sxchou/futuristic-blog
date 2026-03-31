#!/bin/sh
echo "Starting application..."
echo "PORT environment variable: ${PORT:-not set}"
echo "Using port: ${PORT:-8000}"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --log-level info

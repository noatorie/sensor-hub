#!/bin/bash
# Production startup script using Uvicorn ASGI server

# Number of worker processes (1 is recommended for hardware access)
WORKERS=${WORKERS:-1}

# Bind address
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-5000}

echo "Starting Sensor Hub with Uvicorn..."
echo "Workers: $WORKERS"
echo "Binding to: $HOST:$PORT"

exec uvicorn main:app \
    --host $HOST \
    --port $PORT \
    --workers $WORKERS \
    --log-level info \
    --access-log


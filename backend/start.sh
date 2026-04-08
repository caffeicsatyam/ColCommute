#!/bin/bash

# Run database migrations
echo "Running alembic migrations..."
alembic upgrade head

# Start the application using uvicorn (which is in requirements.txt)
# Use $PORT environment variable, default to 8080
echo "Starting Uvicorn server on port ${PORT:-8080}..."
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}

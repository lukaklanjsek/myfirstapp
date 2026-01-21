# Dockerfile
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Environment variables configuration
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create the app directory
RUN mkdir /app
WORKDIR /app

# Copy the Django project  and install dependencies
COPY .. /app/
RUN uv sync --frozen

EXPOSE 8000
# Start the application
CMD ["/app/start-database.sh"]

#!/bin/sh

if [ ! -f "db.sqlite3" ]; then
  echo "Creating database..."
  uv run manage.py makemigrations
  uv run manage.py migrate

  export DJANGO_SUPERUSER_PASSWORD=admin
  uv run manage.py createsuperuser --noinput --username admin --email admin@example.com

  echo "DB created..."

fi

echo "Starting server..."
uv run manage.py runserver 0.0.0.0:8000

#!/bin/bash

# cleanup
rm secondapp/migrations/0*.py
rm db.sqlite3

# setup new db
uv run manage.py makemigrations
uv run manage.py migrate
uv run manage.py loaddata secondapp/fixtures/secondapp/*.json

# start server
uv run manage.py runserver

#!/usr/bin/env bash

cd backend
poetry run python3 manage.py migrate --noinput
poetry run gunicorn --bind 0.0.0.0:8000 backend.wsgi --workers 3

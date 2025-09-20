#!/usr/bin/env bash

cd backend
poetry run python3 manage.py migrate --noinput
poetry run python3 manage.py runserver 0.0.0.0:8000
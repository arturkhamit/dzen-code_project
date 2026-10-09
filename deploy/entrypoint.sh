#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Replace the shell so the ASGI server receives shutdown signals directly.
exec "$@"

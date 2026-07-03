#!/usr/bin/env bash
set -e

# Wait for Postgres to accept connections (simple retry loop).
if [ -n "$DATABASE_URL" ]; then
  echo "Waiting for database…"
  python - <<'PY'
import os, time, sys
import psycopg
url = os.environ.get("DATABASE_URL", "")
for i in range(30):
    try:
        psycopg.connect(url, connect_timeout=2).close()
        print("Database is up.")
        sys.exit(0)
    except Exception as e:  # noqa
        time.sleep(2)
print("Database not reachable, continuing anyway.")
PY
fi

# Apply migrations and collect static on boot (idempotent). Skipped for the
# Celery worker (RUN_MIGRATIONS=0) so only the web service runs migrations.
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput || true

  # Optional demo data seeding.
  if [ "${SEED_DEMO:-0}" = "1" ]; then
    echo "Seeding demo data…"
    python manage.py seed_demo || true
  fi
fi

exec "$@"

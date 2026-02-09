#!/usr/bin/env bash
set -eo pipefail

# Remove SQLite files
find . -name "db.sqlite3" -o -name "*.sqlite3" -o -name "*.sqlite" -print -delete

# Remove references in tracked files
if command -v rg >/dev/null 2>&1; then
  rg -i "sqlite" -l . | while read -r file; do
    # Skip virtual environments and cache directories
    case "$file" in
      */.venv/*|*/venv/*|*/ENV/*|*/__pycache__/*) continue ;;
    esac
    sed -i.bak '/sqlite/Id' "$file" || true
    rm -f "${file}.bak" || true
  done
fi

# Verify PostgreSQL-only DATABASE_URL
python - <<'PYCODE'
import os, sys, dj_database_url
url = os.environ.get("DATABASE_URL")
if not url:
    sys.exit("DATABASE_URL missing")
cfg = dj_database_url.config(env="DATABASE_URL")
engine = cfg.get("ENGINE")
if engine != "django.db.backends.postgresql":
    sys.exit(f"ENGINE must be postgresql, got {engine}")
print("DATABASE_URL OK and PostgreSQL enforced")
PYCODE

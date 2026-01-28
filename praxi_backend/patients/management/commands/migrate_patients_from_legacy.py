from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Iterator

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from praxi_backend.patients.models import Patient


@dataclass(frozen=True)
class LegacyPatientRow:
    id: int
    first_name: str
    last_name: str
    birth_date: date | None
    gender: str | None
    phone: str | None
    email: str | None
    created_at: datetime | None
    updated_at: datetime | None


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            # Accept "YYYY-MM-DD" and ISO.
            return date.fromisoformat(value[:10])
        except Exception:
            return None
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        s = value.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            return None
    else:
        return None

    if timezone.is_naive(dt) and timezone.get_current_timezone() is not None:
        try:
            return timezone.make_aware(dt, timezone.get_current_timezone())
        except Exception:
            return dt
    return dt


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _iter_sqlite_patients(sqlite_path: str, *, table: str) -> Iterator[LegacyPatientRow]:
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        # Try to select the superset of columns; SQLite will error if columns don't exist.
        # We therefore introspect available columns first.
        cols = [r[1] for r in cur.execute(f"PRAGMA table_info({table});").fetchall()]
        if not cols:
            raise CommandError(f"SQLite table '{table}' not found or has no columns")

        wanted = [
            ("id", "id"),
            ("first_name", "first_name"),
            ("last_name", "last_name"),
            ("birth_date", "birth_date"),
            ("gender", "gender"),
            ("phone", "phone"),
            ("email", "email"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ]
        select_cols = [name for name, _ in wanted if name in cols]

        # Minimal compatibility for earlier legacy schema.
        if "id" not in select_cols:
            raise CommandError(f"SQLite table '{table}' must have an 'id' column")
        if "first_name" not in select_cols or "last_name" not in select_cols:
            raise CommandError(f"SQLite table '{table}' must have 'first_name' and 'last_name' columns")

        sql = f"SELECT {', '.join(select_cols)} FROM {table} ORDER BY id"
        for row in cur.execute(sql):
            pid = int(row["id"])
            yield LegacyPatientRow(
                id=pid,
                first_name=str(row.get("first_name") or "").strip(),
                last_name=str(row.get("last_name") or "").strip(),
                birth_date=_parse_date(row.get("birth_date")),
                gender=_safe_str(row.get("gender")),
                phone=_safe_str(row.get("phone")),
                email=_safe_str(row.get("email")),
                created_at=_parse_datetime(row.get("created_at")),
                updated_at=_parse_datetime(row.get("updated_at")),
            )
    finally:
        conn.close()


def _iter_postgres_patients(conninfo: str, *, table: str) -> Iterator[LegacyPatientRow]:
    """Read legacy patients from PostgreSQL via psycopg/psycopg2."""

    try:
        import psycopg  # type: ignore

        _connect = psycopg.connect  # psycopg3
    except Exception:  # pragma: no cover
        try:
            import psycopg2  # type: ignore

            _connect = psycopg2.connect
        except Exception as e:
            raise CommandError(
                "PostgreSQL import requires psycopg (v3) or psycopg2 to be installed"
            ) from e

    with _connect(conninfo) as conn:
        with conn.cursor() as cur:
            # Assume the unified schema (may have more columns; we only read the common subset).
            cur.execute(
                f"""
                SELECT id, first_name, last_name, birth_date, gender, phone, email, created_at, updated_at
                FROM {table}
                ORDER BY id;
                """.strip()
            )
            for (
                pid,
                first_name,
                last_name,
                birth_date,
                gender,
                phone,
                email,
                created_at,
                updated_at,
            ) in cur.fetchall():
                yield LegacyPatientRow(
                    id=int(pid),
                    first_name=(first_name or "").strip(),
                    last_name=(last_name or "").strip(),
                    birth_date=_parse_date(birth_date),
                    gender=_safe_str(gender),
                    phone=_safe_str(phone),
                    email=_safe_str(email),
                    created_at=_parse_datetime(created_at),
                    updated_at=_parse_datetime(updated_at),
                )


def _upsert_patients(rows: Iterable[LegacyPatientRow], *, chunk_size: int = 1000) -> dict[str, int]:
    created = 0
    updated = 0
    skipped = 0

    batch: list[LegacyPatientRow] = []

    def flush(batch_rows: list[LegacyPatientRow]):
        nonlocal created, updated, skipped
        if not batch_rows:
            return

        ids = [r.id for r in batch_rows]
        existing = {
            p.id: p
            for p in Patient.objects.using("default").filter(id__in=ids)
        }

        to_create: list[Patient] = []
        to_update: list[Patient] = []

        for r in batch_rows:
            if r.id <= 0:
                skipped += 1
                continue

            defaults = {
                "first_name": r.first_name or "Unknown",
                "last_name": r.last_name or "Unknown",
                "birth_date": r.birth_date,
                "gender": r.gender,
                "phone": r.phone,
                "email": r.email,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }

            obj = existing.get(r.id)
            if obj is None:
                to_create.append(Patient(id=r.id, **defaults))
            else:
                for k, v in defaults.items():
                    setattr(obj, k, v)
                to_update.append(obj)

        if to_create:
            # ignore_conflicts=True means we cannot trust len(to_create) as actually created.
            before_ids = set(
                Patient.objects.using("default").filter(id__in=[p.id for p in to_create]).values_list("id", flat=True)
            )
            Patient.objects.using("default").bulk_create(to_create, ignore_conflicts=True)
            after_ids = set(
                Patient.objects.using("default").filter(id__in=[p.id for p in to_create]).values_list("id", flat=True)
            )
            # Count IDs that appeared due to this batch.
            created += max(0, len(after_ids - before_ids))

        if to_update:
            Patient.objects.using("default").bulk_update(
                to_update,
                fields=[
                    "first_name",
                    "last_name",
                    "birth_date",
                    "gender",
                    "phone",
                    "email",
                    "created_at",
                    "updated_at",
                ],
            )
            updated += len(to_update)

    for row in rows:
        batch.append(row)
        if len(batch) >= chunk_size:
            flush(batch)
            batch = []

    flush(batch)

    return {"created": created, "updated": updated, "skipped": skipped}


class Command(BaseCommand):
    help = (
        "Import legacy patients into the unified managed patients table (default DB). "
        "Keeps IDs stable."
    )

    def add_arguments(self, parser):
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument(
            "--sqlite-path",
            help="Path to a legacy SQLite database file containing a patients table.",
        )
        source.add_argument(
            "--postgres-conninfo",
            help=(
                "PostgreSQL conninfo string for the legacy DB (e.g. 'dbname=... user=... host=...')."
            ),
        )

        parser.add_argument(
            "--table",
            default=None,
            help=(
                "Legacy table name to read from. "
                "Defaults to 'legacy_patients' if present in SQLite dev DB, otherwise 'patients'."
            ),
        )

        parser.add_argument(
            "--chunk-size",
            type=int,
            default=1000,
            help="Batch size for upserts (default: 1000).",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate input, but do not write to the database.",
        )

    def handle(self, *args, **options):
        sqlite_path: str | None = options.get("sqlite_path")
        pg_conninfo: str | None = options.get("postgres_conninfo")
        table_opt: str | None = options.get("table")
        chunk_size: int = options.get("chunk_size")
        dry_run: bool = bool(options.get("dry_run"))

        if chunk_size <= 0:
            raise CommandError("--chunk-size must be > 0")

        if sqlite_path:
            table = table_opt
            if not table:
                # Prefer the renamed table name produced by the migration, but fall back.
                conn = sqlite3.connect(sqlite_path)
                try:
                    cur = conn.cursor()
                    tables = {
                        r[0]
                        for r in cur.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        ).fetchall()
                    }
                finally:
                    conn.close()
                table = "legacy_patients" if "legacy_patients" in tables else "patients"

            self.stdout.write(f"Reading legacy patients from SQLite: {sqlite_path} (table={table})")
            rows = _iter_sqlite_patients(sqlite_path, table=table)

        elif pg_conninfo:
            table = table_opt or "patients"
            self.stdout.write(f"Reading legacy patients from PostgreSQL (table={table})")
            rows = _iter_postgres_patients(pg_conninfo, table=table)
        else:
            raise CommandError("One of --sqlite-path or --postgres-conninfo is required")

        if dry_run:
            # Exhaust iterator to validate.
            count = 0
            for _ in rows:
                count += 1
            self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Parsed {count} legacy patients"))
            return

        self.stdout.write(f"Upserting into default DB (chunk_size={chunk_size})...")
        with transaction.atomic(using="default"):
            stats = _upsert_patients(rows, chunk_size=chunk_size)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported legacy patients: created={stats['created']} updated={stats['updated']} skipped={stats['skipped']}"
            )
        )

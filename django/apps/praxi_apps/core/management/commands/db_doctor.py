from __future__ import annotations

import json
from datetime import datetime, timezone

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = "Validate PostgreSQL migration state and primary-key sequence alignment"

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            help="Emit machine-readable JSON output.",
        )

    def handle(self, *args, **options):
        as_json = options.get("json", False)

        errors: list[str] = []
        warnings: list[str] = []
        checks: list[dict] = []

        migration_ok, pending = self._check_migrations()
        checks.append(
            {
                "name": "pending_migrations",
                "ok": migration_ok,
                "message": "No pending migrations" if migration_ok else "Pending migrations detected",
                "details": pending,
            }
        )
        if not migration_ok:
            errors.append("Unapplied migrations exist")

        sequence_issues = self._check_sequences()
        checks.append(
            {
                "name": "pk_sequences_aligned",
                "ok": len(sequence_issues) == 0,
                "message": "All integer PK sequences aligned"
                if not sequence_issues
                else "Sequence drift detected",
                "details": sequence_issues,
            }
        )
        if sequence_issues:
            errors.append("One or more primary-key sequences are behind table max(id)")

        payload = {
            "status": "ok" if not errors else "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "errors": errors,
            "warnings": warnings,
            "checks": checks,
        }

        if as_json:
            self.stdout.write(json.dumps(payload, indent=2))
        else:
            self.stdout.write(self._format_human(payload))

        if errors:
            raise CommandError("db_doctor detected blocking issues")

    def _check_migrations(self) -> tuple[bool, list[str]]:
        try:
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            pending = [f"{migration[0].app_label}.{migration[0].name}" for migration in plan]
            return len(pending) == 0, pending
        except Exception as exc:
            return False, [f"migration_state_unavailable: {exc}"]

    def _check_sequences(self) -> list[dict]:
        query = """
            SELECT c.table_name
            FROM information_schema.columns c
            JOIN information_schema.table_constraints tc
              ON tc.table_schema = c.table_schema
             AND tc.table_name = c.table_name
             AND tc.constraint_type = 'PRIMARY KEY'
            JOIN information_schema.key_column_usage kcu
              ON kcu.constraint_name = tc.constraint_name
             AND kcu.table_schema = tc.table_schema
             AND kcu.table_name = tc.table_name
             AND kcu.column_name = c.column_name
            WHERE c.table_schema = 'public'
              AND c.column_name = 'id'
              AND c.data_type IN ('integer', 'bigint')
            ORDER BY c.table_name
        """

        issues: list[dict] = []

        with connection.cursor() as cursor:
            cursor.execute(query)
            table_rows = [row[0] for row in cursor.fetchall()]

        with connection.cursor() as cursor:
            for table_name in table_rows:
                cursor.execute("SELECT pg_get_serial_sequence(%s, 'id')", [f"public.{table_name}"])
                sequence_name = cursor.fetchone()[0]
                if not sequence_name:
                    continue

                cursor.execute(f'SELECT COALESCE(MAX(id), 0) FROM "{table_name}"')
                max_id = int(cursor.fetchone()[0] or 0)

                cursor.execute(f'SELECT last_value, is_called FROM {sequence_name}')
                last_value, is_called = cursor.fetchone()
                last_value = int(last_value)
                next_value = last_value + 1 if is_called else last_value

                if next_value <= max_id:
                    issues.append(
                        {
                            "table": table_name,
                            "sequence": sequence_name,
                            "max_id": max_id,
                            "last_value": last_value,
                            "is_called": bool(is_called),
                            "next_value": next_value,
                            "repair_sql": f"SELECT setval('{sequence_name}', {max_id}, true);",
                        }
                    )

        return issues

    def _format_human(self, payload: dict) -> str:
        lines = ["DB Doctor report", f"status={payload['status']}"]
        for check in payload["checks"]:
            icon = "OK" if check["ok"] else "FAIL"
            lines.append(f"[{icon}] {check['name']}: {check['message']}")
            details = check.get("details") or []
            for detail in details[:20]:
                lines.append(f"  - {detail}")
        if payload["errors"]:
            lines.append("Errors:")
            for error in payload["errors"]:
                lines.append(f"- {error}")
        return "\n".join(lines)

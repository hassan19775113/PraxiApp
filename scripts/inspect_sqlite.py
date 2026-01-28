from __future__ import annotations

import os
import sqlite3


def main() -> None:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dev.sqlite3")
    print("sqlite exists:", os.path.exists(path), "size:", os.path.getsize(path) if os.path.exists(path) else None)
    if not os.path.exists(path):
        return

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print("tables:", len(tables))

    priority = [
        "core_user",
        "core_role",
        "core_auditlog",
        "appointments_appointment",
        "appointments_operation",
        "patients",
        "patient_notes",
        "patient_documents",
        "django_migrations",
        "django_admin_log",
    ]

    seen: set[str] = set()
    for t in priority:
        if t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"{t}:", cur.fetchone()[0])
            seen.add(t)

    print("---")

    shown = 0
    for t in tables:
        if t in seen:
            continue
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        c = int(cur.fetchone()[0])
        if c:
            print(f"{t}: {c}")
            shown += 1
            if shown >= 30:
                break

    conn.close()


if __name__ == "__main__":
    main()

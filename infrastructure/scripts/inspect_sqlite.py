from __future__ import annotations

import json
import os
from collections import Counter


def _find_latest_domain_dump() -> str | None:
    """Return path to the newest backups/**/sqlite_dump_domain.json if present."""
    root = os.path.dirname(os.path.dirname(__file__))
    backups_dir = os.path.join(root, "backups")
    if not os.path.isdir(backups_dir):
        return None

    candidates: list[str] = []
    for name in os.listdir(backups_dir):
        # Folder naming convention: sqlite_to_postgres_YYYY-MM-DD
        if not name.startswith("sqlite_to_postgres_"):
            continue
        path = os.path.join(backups_dir, name, "sqlite_dump_domain.json")
        if os.path.isfile(path):
            candidates.append(path)

    if not candidates:
        return None
    # Lexicographic works with YYYY-MM-DD suffix.
    return sorted(candidates)[-1]


def main() -> None:
    dump_path = _find_latest_domain_dump()
    print("domain dump found:", bool(dump_path), "path:", dump_path)
    if not dump_path:
        return

    with open(dump_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    models = Counter(item.get("model") for item in items if isinstance(item, dict))
    print("objects:", sum(models.values()))
    print("models:", len(models))

    # Print a few high-signal model counts.
    for key in [
        "core.role",
        "core.user",
        "patients.patient",
        "appointments.appointment",
        "appointments.operation",
        "core.auditlog",
    ]:
        if key in models:
            print(f"{key}:", models[key])

    print("--- top 30 models ---")
    for model, count in models.most_common(30):
        print(f"{model}: {count}")


if __name__ == "__main__":
    main()

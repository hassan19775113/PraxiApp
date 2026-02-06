from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def _type_sql(col: dict[str, Any]) -> str:
    data_type = (col.get("data_type") or "").strip()
    max_len = col.get("character_maximum_length")
    precision = col.get("numeric_precision")
    scale = col.get("numeric_scale")

    dt = data_type.lower()

    if dt in {"character varying", "varchar"}:
        return f"varchar({int(max_len)})" if max_len else "varchar"
    if dt in {"character", "char"}:
        return f"char({int(max_len)})" if max_len else "char"
    if dt in {"numeric", "decimal"}:
        if precision is not None and scale is not None:
            return f"numeric({int(precision)},{int(scale)})"
        if precision is not None:
            return f"numeric({int(precision)})"
        return "numeric"

    # Normalize a few common Postgres spellings
    if dt == "timestamp with time zone":
        return "timestamptz"
    if dt == "timestamp without time zone":
        return "timestamp"
    if dt == "time with time zone":
        return "timetz"
    if dt == "time without time zone":
        return "time"

    # Everything else: keep as-is (already Postgres-ish)
    return data_type


def _sql_lines_for_tables(
    table_names: Iterable[str],
    columns_by_table: dict[str, list[dict[str, Any]]],
    schema: str,
    *,
    drop_existing: bool,
) -> list[str]:
    lines: list[str] = []

    if drop_existing:
        # Drop in reverse-ish name order to reduce FK drop errors (not guaranteed).
        for table in sorted(table_names, reverse=True):
            lines.append(f"DROP TABLE IF EXISTS {schema}.{table} CASCADE;")
        lines.append("")

    for table in sorted(table_names):
        cols = sorted(columns_by_table.get(table, []), key=lambda c: int(c.get("ordinal_position") or 0))
        if not cols:
            # Defensive: schema export should include columns, but don't crash.
            continue

        lines.append(f"CREATE TABLE IF NOT EXISTS {schema}.{table} (")

        col_lines: list[str] = []
        for col in cols:
            col_name = col["column_name"]
            col_type = _type_sql(col)
            pieces = [f"  {col_name} {col_type}"]

            default = col.get("column_default")
            if default not in (None, ""):
                pieces.append(f"DEFAULT {default}")

            if (col.get("is_nullable") or "").upper() == "NO":
                pieces.append("NOT NULL")

            col_lines.append(" ".join(pieces))

        lines.append(",\n".join(col_lines))
        lines.append(");")
        lines.append("")

    return lines


def _group_by_table(items: list[dict[str, Any]], table_key: str = "table_name") -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        table = item.get(table_key)
        if table:
            grouped[str(table)].append(item)
    return dict(grouped)


def _sql_lines_for_primary_keys(primary_keys: list[dict[str, Any]], schema: str) -> list[str]:
    by_table = defaultdict(list)
    for pk in primary_keys:
        table = pk.get("table_name")
        col = pk.get("column_name")
        if table and col:
            by_table[str(table)].append(str(col))

    lines: list[str] = []
    for table in sorted(by_table.keys()):
        cols = ", ".join(by_table[table])
        # Use deterministic PK constraint names.
        lines.append(
            f"ALTER TABLE {schema}.{table} "
            f"ADD CONSTRAINT {table}_pkey PRIMARY KEY ({cols});"
        )

    if lines:
        lines.append("")

    return lines


def _sql_lines_for_foreign_keys(foreign_keys: list[dict[str, Any]], schema: str) -> list[str]:
    lines: list[str] = []

    for fk in foreign_keys:
        table = fk.get("table_name")
        col = fk.get("column_name")
        foreign_table = fk.get("foreign_table")
        foreign_col = fk.get("foreign_column")
        if not (table and col and foreign_table and foreign_col):
            continue

        constraint_name = f"fk_{table}_{col}"
        lines.append(
            f"ALTER TABLE {schema}.{table} "
            f"ADD CONSTRAINT {constraint_name} "
            f"FOREIGN KEY ({col}) REFERENCES {schema}.{foreign_table} ({foreign_col});"
        )

    if lines:
        lines.append("")

    return lines


def _sql_lines_for_indexes(indexes: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for idx in indexes:
        name = (idx.get("index_name") or "").strip()
        definition = (idx.get("index_definition") or "").strip()
        if not definition:
            continue

        # If we already add a PRIMARY KEY constraint, Postgres will create its own index.
        if name.endswith("_pkey"):
            continue

        if not definition.endswith(";"):
            definition += ";"
        lines.append(definition)

    if lines:
        lines.append("")

    return lines


def build_sql(schema_json: dict[str, Any], *, schema: str, drop_existing: bool) -> str:
    tables = [t["name"] for t in schema_json.get("tables", []) if isinstance(t, dict) and t.get("name")]

    columns_by_table: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for col in schema_json.get("columns", []):
        if not isinstance(col, dict):
            continue
        table = col.get("table_name")
        if table:
            columns_by_table[str(table)].append(col)

    primary_keys = schema_json.get("primary_keys", []) or []
    foreign_keys = schema_json.get("foreign_keys", []) or []
    indexes = schema_json.get("indexes", []) or []

    lines: list[str] = []
    lines.append("-- Generated from infrastructure/docs/public_schema.json")
    lines.append("-- Note: CHECK/constraint definitions may not be fully represented in the JSON export.")
    lines.append("BEGIN;")
    lines.append("")

    lines.extend(
        _sql_lines_for_tables(
            tables,
            dict(columns_by_table),
            schema,
            drop_existing=drop_existing,
        )
    )
    lines.extend(_sql_lines_for_primary_keys(list(primary_keys), schema))
    lines.extend(_sql_lines_for_foreign_keys(list(foreign_keys), schema))
    lines.extend(_sql_lines_for_indexes(list(indexes)))

    lines.append("COMMIT;")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate PostgreSQL DDL (schema-only) from infrastructure/docs/public_schema.json",
    )
    parser.add_argument(
        "--input",
        default=str(Path("infrastructure") / "docs" / "public_schema.json"),
        help="Path to the public_schema.json file",
    )
    parser.add_argument(
        "--output",
        default=str(Path("infrastructure") / "docs" / "public_schema.generated.sql"),
        help="Where to write the generated .sql file",
    )
    parser.add_argument(
        "--schema",
        default="public",
        help="Target schema name (default: public)",
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Add DROP TABLE ... CASCADE statements before creating tables",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    schema_json = json.loads(input_path.read_text(encoding="utf-8"))
    sql = build_sql(schema_json, schema=args.schema, drop_existing=args.drop_existing)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sql, encoding="utf-8")

    print(f"Wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

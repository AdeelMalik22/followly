#!/home/enigmatix/followly/.venv/bin/python
"""Compare a migrated PostgreSQL database and validate tenant ownership."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

from sqlalchemy import create_engine, inspect, text


def table_names(engine):
    return set(inspect(engine).get_table_names())


def count_rows(connection, table: str, business_id: int | None = None) -> int:
    query = f'SELECT count(*) FROM "{table}"'
    parameters = {}
    if business_id is not None:
        query += " WHERE business_id = :business_id"
        parameters["business_id"] = business_id
    return int(connection.execute(text(query), parameters).scalar_one())


def business_scoped_tables(engine, tables):
    inspector = inspect(engine)
    return {
        table for table in tables
        if any(column["name"] == "business_id" for column in inspector.get_columns(table))
    }


def collect_report(url: str, selected_business_ids: set[int] | None):
    engine = create_engine(url)
    tables = table_names(engine)
    scoped = business_scoped_tables(engine, tables)
    report = {"tables": {}, "ownership_errors": []}
    with engine.connect() as connection:
        for table in sorted(tables):
            if table == "alembic_version":
                continue
            total = count_rows(connection, table)
            item = {"total": total}
            if table in scoped:
                rows = connection.execute(
                    text(f'SELECT business_id, count(*) FROM "{table}" GROUP BY business_id')
                ).all()
                item["by_business"] = {str(row[0]): row[1] for row in rows}
                orphaned = connection.execute(
                    text(
                        f'SELECT count(*) FROM "{table}" t '
                        'WHERE t.business_id IS NOT NULL '
                        'AND NOT EXISTS (SELECT 1 FROM businesses b WHERE b.id = t.business_id)'
                    )
                ).scalar_one()
                if orphaned:
                    report["ownership_errors"].append({"table": table, "orphaned_rows": orphaned})
                if selected_business_ids:
                    item["selected_business_rows"] = {
                        str(business_id): count_rows(connection, table, business_id)
                        for business_id in sorted(selected_business_ids)
                    }
            report["tables"][table] = item
        for table, parent in (("messages", "conversations"), ("tool_call_audits", "conversations")):
            if table not in tables or parent not in tables:
                continue
            orphaned = connection.execute(
                text(
                    f'SELECT count(*) FROM "{table}" child '
                    f'WHERE NOT EXISTS (SELECT 1 FROM "{parent}" parent '
                    'WHERE parent.id = child.conversation_id)'
                )
            ).scalar_one()
            if orphaned:
                report["ownership_errors"].append({"table": table, "orphaned_parent_rows": orphaned})
    engine.dispose()
    return report


def compare_reports(source, target):
    differences = []
    for table in sorted(set(source["tables"]) | set(target["tables"])):
        source_item = source["tables"].get(table, {})
        target_item = target["tables"].get(table, {})
        if source_item.get("total") != target_item.get("total"):
            differences.append({"table": table, "source": source_item.get("total", 0), "target": target_item.get("total", 0)})
        if source_item.get("by_business") != target_item.get("by_business"):
            differences.append({"table": table, "source_by_business": source_item.get("by_business", {}), "target_by_business": target_item.get("by_business", {})})
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--business-id", type=int, action="append", dest="business_ids")
    args = parser.parse_args()
    selected = set(args.business_ids or [])
    source = collect_report(args.source_url, selected)
    target = collect_report(args.target_url, selected)
    differences = compare_reports(source, target)
    result = {"source": source, "target": target, "count_differences": differences}
    print(json.dumps(result, indent=2, sort_keys=True))
    if source["ownership_errors"] or target["ownership_errors"] or differences:
        print("Tenant migration verification failed", file=sys.stderr)
        return 1
    print("Tenant migration verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

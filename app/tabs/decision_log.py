"""Decision log tab. The app shell calls render(). Reads closecall_decisions; never writes."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EMPTY_MESSAGE = "No decisions yet."

DISPLAY_COLUMNS = (
    ("segment_id", "Segment"),
    ("action", "Action"),
    ("verdict_at_decision", "Verdict at decision"),
    ("prompt_version", "Prompt version"),
    ("reviewer", "Reviewer"),
    ("decided_at", "Time"),
    ("reason", "Reason"),
)

# Stand-in rows used only when the team database cannot be read.
# Reviewer "test" must stay hidden. Reasons are placeholders, not model output.
DEMO_DECISIONS = (
    {
        "decision_id": "demo-3",
        "segment_id": "demo_seg_3",
        "action": "reject",
        "reason": "Practice click. Hidden from the log.",
        "reviewer": "test",
        "verdict_at_decision": "NO_CONFLICT",
        "prompt_version": "demo",
        "decided_at": "2026-10-09T15:00:00Z",
    },
    {
        "decision_id": "demo-2",
        "segment_id": "demo_seg_4",
        "action": "reject",
        "reason": "Stand-in reviewer note.",
        "reviewer": "sam",
        "verdict_at_decision": "CLOSE_CALL",
        "prompt_version": "demo",
        "decided_at": "2026-10-09T14:05:00Z",
    },
    {
        "decision_id": "demo-1",
        "segment_id": "demo_seg_1",
        "action": "approve",
        "reason": "Stand-in reviewer note.",
        "reviewer": "alex",
        "verdict_at_decision": "CLOSE_CALL",
        "prompt_version": "demo",
        "decided_at": "2026-10-09T13:10:00Z",
    },
)


def is_test_reviewer(name):
    return str(name or "").strip().casefold() == "test"


def _parse_time(value):
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _sort_key(row):
    parsed = _parse_time(row.get("decided_at"))
    if parsed is None:
        return (0, "")
    return (1, parsed.isoformat())


def visible_decisions(rows):
    kept = [row for row in rows or [] if not is_test_reviewer(row.get("reviewer"))]
    return sorted(kept, key=_sort_key, reverse=True)


def display_records(rows):
    records = []
    for row in visible_decisions(rows):
        record = {}
        for key, label in DISPLAY_COLUMNS:
            if key == "decided_at":
                record[label] = _display_time(row.get(key))
            else:
                record[label] = _cell(row.get(key))
        records.append(record)
    return records


def _cell(value):
    if value is None:
        return ""
    return str(value)


def _display_time(value):
    parsed = _parse_time(value)
    if parsed is None:
        return _cell(value)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
        return parsed.strftime("%Y-%m-%d %H:%M UTC")
    return parsed.strftime("%Y-%m-%d %H:%M")


def bucket_and_schema(schema_text="", env=None):
    env = os.environ if env is None else env
    bucket = (env.get("VASTDB_BUCKET") or env.get("VAST_BUCKET") or "").strip()
    schema = (env.get("VASTDB_SCHEMA") or env.get("VAST_SCHEMA") or "").strip()
    found = {}
    for line in (schema_text or "").splitlines():
        match = re.match(
            r"(?i)^[\s\-\*\|>]*\**\s*(bucket|schema)\**\s*[:=]\s*`?([^`\s]+)`?\s*$",
            line,
        )
        if match and match.group(1).lower() not in found:
            found[match.group(1).lower()] = match.group(2).strip().strip("`")
    return bucket or found.get("bucket", ""), schema or found.get("schema", "")


def _schema_text():
    path = REPO_ROOT / "notes" / "schema.md"
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def read_table(table_name):
    """Return rows from VastDB, or None when the table cannot be read."""
    bucket, schema = bucket_and_schema(_schema_text())
    if not bucket or not schema:
        return None
    try:
        import vastdb
    except ImportError:
        return None
    try:
        session = vastdb.connect(timeout=(3, 15))
        with session.transaction() as tx:
            table = tx.bucket(bucket).schema(schema).table(table_name)
            result = table.select().read_all()
        if hasattr(result, "to_pylist"):
            return result.to_pylist()
    except Exception:
        return None
    return None


def load_decisions():
    rows = read_table("closecall_decisions")
    if rows is None:
        return list(DEMO_DECISIONS), "demo"
    return rows, "database"


def _apply_style():
    try:
        from app.tabs.counters import apply_style
    except ImportError:
        from counters import apply_style

    apply_style()


def render():
    import streamlit as st

    _apply_style()
    st.subheader("Decision log")
    rows, source = load_decisions()
    if source == "demo":
        st.info("DEMO DATA")
    records = display_records(rows)
    if not records:
        st.write(EMPTY_MESSAGE)
        return
    st.dataframe(records, hide_index=True, width="stretch")


def _self_check():
    visible = visible_decisions(DEMO_DECISIONS)
    reviewers = [row["reviewer"] for row in visible]
    if reviewers != ["sam", "alex"]:
        raise SystemExit(f"expected newest real reviewers sam then alex, got {reviewers}")
    if any(is_test_reviewer(name) for name in reviewers):
        raise SystemExit("reviewer test was not hidden")
    if display_records([]) != []:
        raise SystemExit("empty decisions should display no rows")
    times = [row["Time"] for row in display_records(DEMO_DECISIONS)]
    if times != ["2026-10-09 14:05 UTC", "2026-10-09 13:10 UTC"]:
        raise SystemExit(f"time display mismatch: {times}")
    bucket, schema = bucket_and_schema("bucket: team-bucket\nschema: closecall\n", env={})
    if (bucket, schema) != ("team-bucket", "closecall"):
        raise SystemExit(f"schema parse failed: {(bucket, schema)}")
    overridden = bucket_and_schema(
        "bucket: from-file\nschema: from-file\n",
        env={"VASTDB_BUCKET": "from-env", "VASTDB_SCHEMA": "env-schema"},
    )
    if overridden != ("from-env", "env-schema"):
        raise SystemExit(f"env override failed: {overridden}")
    print("decision_log ok", len(visible), "visible rows")


if __name__ == "__main__":
    _self_check()

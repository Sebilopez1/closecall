"""Counter row. The app shell calls render() and places it above the tabs."""

from datetime import datetime

COUNTER_LABELS = (
    "Clips checked",
    "Close calls found",
    "Hazards found",
    "Waiting for review",
    "Decisions made",
)

# Stand-in verdicts. Counted by hand in _self_check: 5 clips, 2 close calls,
# 2 hazards, 2 waiting, 2 decisions (reviewer test does not count).
DEMO_VERDICTS = (
    {
        "segment_id": "demo_seg_1",
        "final_answer": "CLOSE_CALL",
        "hazard": "none",
        "created_at": "2026-10-09T12:00:00Z",
    },
    {
        "segment_id": "demo_seg_2",
        "final_answer": "CANT_TELL",
        "hazard": "none",
        "created_at": "2026-10-09T12:01:00Z",
    },
    {
        "segment_id": "demo_seg_3",
        "final_answer": "NO_CONFLICT",
        "hazard": "wires",
        "created_at": "2026-10-09T12:02:00Z",
    },
    {
        "segment_id": "demo_seg_4",
        "final_answer": "CLOSE_CALL",
        "hazard": "debris",
        "created_at": "2026-10-09T12:03:00Z",
    },
    {
        "segment_id": "demo_seg_5",
        "final_answer": "NO_CONFLICT",
        "hazard": "none",
        "created_at": "2026-10-09T12:04:00Z",
    },
)

try:
    from app.tabs.decision_log import DEMO_DECISIONS, read_table, visible_decisions
except ImportError:
    from decision_log import DEMO_DECISIONS, read_table, visible_decisions


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


STYLE = """
<style>
.block-container { padding-top: 1.4rem; padding-bottom: 2.2rem; max-width: 1080px; }
div[data-testid="stMetric"] {
  background: #f4f8f8;
  border: 1px solid #d5e2e4;
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
  font-size: 1.6rem;
  font-variant-numeric: tabular-nums;
}
div[data-testid="stMetricLabel"] { font-size: 0.95rem; }
[data-testid="stDataFrame"] { border-radius: 10px; }
div[data-testid="stMarkdownContainer"] p { line-height: 1.55; font-size: 1.05rem; }
h3 { letter-spacing: -0.01em; }
</style>
"""


def apply_style():
    import streamlit as st

    st.markdown(STYLE, unsafe_allow_html=True)


def _time_key(row):
    parsed = _parse_time(row.get("created_at"))
    if parsed is None:
        return (0, "")
    return (1, parsed.isoformat())


def latest_verdicts(rows):
    chosen = {}
    order = []
    for index, row in enumerate(rows or []):
        key = str(row.get("segment_id") or f"row-{index}")
        if key not in chosen or _time_key(row) >= _time_key(chosen[key]):
            if key not in chosen:
                order.append(key)
            chosen[key] = row
    return [chosen[key] for key in order]


def _has_hazard(row):
    hazard = str(row.get("hazard") or "").strip().casefold()
    return hazard not in {"", "none"}


def in_review_queue(row):
    answer = str(row.get("final_answer") or "").strip()
    return answer in {"CLOSE_CALL", "CANT_TELL"} or _has_hazard(row)


def compute_counts(verdicts, decisions):
    clips = latest_verdicts(verdicts)
    decided = {
        str(row.get("segment_id"))
        for row in visible_decisions(decisions)
        if row.get("segment_id")
    }
    return {
        "Clips checked": len(clips),
        "Close calls found": sum(
            1 for row in clips if str(row.get("final_answer") or "").strip() == "CLOSE_CALL"
        ),
        "Hazards found": sum(1 for row in clips if _has_hazard(row)),
        "Waiting for review": sum(
            1
            for row in clips
            if in_review_queue(row) and str(row.get("segment_id") or "") not in decided
        ),
        "Decisions made": len(visible_decisions(decisions)),
    }


def load_snapshot():
    verdicts = read_table("closecall_verdicts")
    decisions = read_table("closecall_decisions")
    if verdicts is None and decisions is None:
        return list(DEMO_VERDICTS), list(DEMO_DECISIONS), "demo"
    return list(verdicts or []), list(decisions or []), "database"


def render():
    import streamlit as st

    apply_style()
    verdicts, decisions, source = load_snapshot()
    counts = compute_counts(verdicts, decisions)
    if source == "demo":
        st.info("DEMO DATA")
    columns = st.columns(len(COUNTER_LABELS), gap="medium")
    for column, label in zip(columns, COUNTER_LABELS):
        with column:
            st.metric(label, counts[label])


def _self_check():
    counts = compute_counts(DEMO_VERDICTS, DEMO_DECISIONS)
    expected = {
        "Clips checked": 5,
        "Close calls found": 2,
        "Hazards found": 2,
        "Waiting for review": 2,
        "Decisions made": 2,
    }
    if counts != expected:
        raise SystemExit(f"manual count mismatch: {counts} != {expected}")
    if counts["Decisions made"] != len(visible_decisions(DEMO_DECISIONS)):
        raise SystemExit("decisions made does not match the decision log")

    duplicate = [
        {
            "segment_id": "a",
            "final_answer": "NO_CONFLICT",
            "hazard": "none",
            "created_at": "2026-10-09T10:00:00Z",
        },
        {
            "segment_id": "a",
            "final_answer": "CLOSE_CALL",
            "hazard": "wires",
            "created_at": "2026-10-09T11:00:00Z",
        },
    ]
    latest = compute_counts(duplicate, [])
    if latest["Clips checked"] != 1 or latest["Close calls found"] != 1:
        raise SystemExit(f"latest-row count failed: {latest}")
    if latest["Hazards found"] != 1 or latest["Waiting for review"] != 1:
        raise SystemExit(f"latest hazard/queue failed: {latest}")

    real = [{"segment_id": "a", "reviewer": "sam", "decided_at": "2026-10-09T12:00:00Z"}]
    cleared = compute_counts(duplicate, real)
    if cleared["Waiting for review"] != 0 or cleared["Decisions made"] != 1:
        raise SystemExit(f"real decision should clear the queue: {cleared}")

    practice = [{"segment_id": "a", "reviewer": " Test ", "decided_at": "2026-10-09T12:00:00Z"}]
    hidden = compute_counts(duplicate, practice)
    if hidden["Waiting for review"] != 1 or hidden["Decisions made"] != 0:
        raise SystemExit(f"test reviewer should not count: {hidden}")
    print("counters ok", counts)


if __name__ == "__main__":
    _self_check()

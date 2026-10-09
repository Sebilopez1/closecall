"""Accuracy tab. The app shell calls render(). Reads results.json; never writes it."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLACEHOLDER = "Results will appear here after scoring"
NOTE = (
    "Measured on our hand-labeled test clips. Ranges are 95% intervals. "
    "Hazard tags aren't scored yet."
)


def results_ready(status_text):
    return "RESULTS READY" in (status_text or "")


def format_metric(block):
    if not isinstance(block, dict):
        return "—"
    try:
        value = float(block["value"])
        low = float(block["low"])
        high = float(block["high"])
        count = int(block["n"])
    except (KeyError, TypeError, ValueError):
        return "—"
    return f"{value:.3f} ({low:.3f}–{high:.3f}), n={count}"


def version_rows(payload):
    rows = []
    for version in payload.get("versions") or []:
        if not isinstance(version, dict):
            continue
        rows.append(
            {
                "Version": str(version.get("name") or ""),
                "Precision": format_metric(version.get("precision")),
                "Recall": format_metric(version.get("recall")),
                "Coverage": format_metric(version.get("coverage")),
            }
        )
    return rows


def hazard_lines(payload):
    hazards = payload.get("hazards_found") or {}
    if not isinstance(hazards, dict):
        return []
    lines = []
    for name in sorted(hazards, key=lambda item: str(item)):
        if str(name).strip().casefold() == "none":
            continue
        lines.append(f"{name}: {hazards[name]}")
    return lines


def load_results():
    status_path = REPO_ROOT / "status" / "scoring.md"
    results_path = REPO_ROOT / "results.json"
    status_text = status_path.read_text(encoding="utf-8") if status_path.is_file() else ""
    if not results_ready(status_text):
        return None, "waiting"
    if not results_path.is_file():
        return None, "missing"
    try:
        payload = json.loads(results_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "unreadable"
    if not isinstance(payload, dict):
        return None, "unreadable"
    return payload, "ready"


def render_ready(payload):
    import streamlit as st

    n_test = payload.get("n_test", "—")
    kappa = payload.get("kappa", "—")
    kappa_text = f"{kappa:.2f}" if isinstance(kappa, (int, float)) else str(kappa)
    st.markdown(f"**Clips in the test** {n_test}")
    st.markdown(f"**Agreement between labelers (kappa)** {kappa_text}")
    hazards = hazard_lines(payload)
    hazard_text = " · ".join(hazards) if hazards else "none recorded"
    st.markdown(f"**Hazards found** {hazard_text}")
    generated = payload.get("generated_at")
    if generated:
        st.caption(f"Scored at {generated}")
    rows = version_rows(payload)
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.write("No versions in results.json.")
    st.caption(NOTE)


def render():
    import streamlit as st

    st.subheader("Accuracy")
    payload, state = load_results()
    if state == "waiting":
        st.write(PLACEHOLDER)
        return
    if state == "missing":
        st.write(PLACEHOLDER)
        st.caption("results.json is not in the repo yet.")
        return
    if state != "ready":
        st.write(PLACEHOLDER)
        st.caption("results.json could not be read.")
        return
    render_ready(payload)


def _self_check():
    if results_ready("still scoring\n"):
        raise SystemExit("placeholder status was treated as ready")
    if not results_ready("13:10 ET — S3 done — RESULTS READY\n"):
        raise SystemExit("RESULTS READY was missed")
    if not results_ready("RESULTS READY v2"):
        raise SystemExit("RESULTS READY v2 was missed")
    metric = format_metric({"value": 0.8, "low": 0.49, "high": 0.943, "n": 10})
    if metric != "0.800 (0.490–0.943), n=10":
        raise SystemExit(f"metric format mismatch: {metric}")
    sample = {
        "n_test": 30,
        "kappa": 0.5,
        "hazards_found": {"wires": 2, "none": 9, "debris": 1},
        "versions": [
            {
                "name": "C — Full CloseCall",
                "precision": {"value": 0.8, "low": 0.49, "high": 0.943, "n": 10},
                "recall": {"value": 0.5, "low": 0.2, "high": 0.8, "n": 8},
                "coverage": {"value": 1, "low": 0.9, "high": 1, "n": 30},
            }
        ],
    }
    lines = hazard_lines(sample)
    if lines != ["debris: 1", "wires: 2"]:
        raise SystemExit(f"hazard lines mismatch: {lines}")
    rows = version_rows(sample)
    if rows[0]["Precision"] != "0.800 (0.490–0.943), n=10":
        raise SystemExit(f"version row mismatch: {rows}")
    if load_results()[1] != "waiting":
        raise SystemExit(f"expected waiting, got {load_results()[1]}")
    print("accuracy ok")


if __name__ == "__main__":
    _self_check()

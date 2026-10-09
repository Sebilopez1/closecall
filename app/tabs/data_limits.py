"""Data & Limits tab. The app shell calls render()."""

TEXT = """CloseCall looks at places and patterns, never people: no face recognition, no license plates,
no tracking anyone. Raw video stays in VAST; only events and decisions are saved. Every action
is approved by a person and logged. Limits: tested on a small hand-labeled set of dashcam
clips; Cosmos can misjudge fast, dark or hidden scenes, so unclear clips go to a person.
Hazard tags are Cosmos's reading of the clip and are not yet scored against hand labels."""


def _apply_style():
    try:
        from app.tabs.counters import apply_style
    except ImportError:
        from counters import apply_style

    apply_style()


def render():
    import streamlit as st

    _apply_style()
    st.subheader("Data & Limits")
    st.markdown(TEXT)


def _self_check():
    required = [
        "no face recognition",
        "no license plates",
        "no tracking anyone",
        "Raw video stays in VAST",
        "Hazard tags are Cosmos's reading of the clip",
        "are not yet scored against hand labels.",
    ]
    missing = [line for line in required if line not in TEXT]
    if missing:
        raise SystemExit(f"Data & Limits text is missing: {missing}")
    print("data_limits text ok")


if __name__ == "__main__":
    _self_check()

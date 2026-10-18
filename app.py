"""Career Radar studio: landing page, four analytical tools and methodology."""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import streamlit as st

from career_radar.normalise import load_taxonomy
from career_radar.ui import home
from career_radar.ui.styles import apply_styles

ROOT = Path(__file__).resolve().parent
DEFAULT_SNAPSHOT = ROOT / "data" / "processed" / "market_snapshot.json"
ROUTES = {"Skill Constellation": "constellation", "Readiness Studio": "readiness", "Career Mobility": "mobility", "JD Diagnostic": "diagnostic"}


def read_snapshot(path: Path) -> tuple[dict | None, str | None]:
    """A missing or malformed local snapshot must not take down unrelated tools."""
    if not path.exists():
        return None, "No market snapshot is loaded. Market-dependent analysis will be unavailable."
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("market"), dict) or not isinstance(payload.get("metadata"), dict):
            raise ValueError("Expected market and metadata objects")
        sample_size = payload["market"].get("sample_size")
        if type(sample_size) is not int or sample_size < 0:
            raise ValueError("Expected an integer sample size")
        for field in ("postings", "evidence"):
            if field in payload:
                if not isinstance(payload[field], list) or any(not isinstance(row, dict) for row in payload[field]):
                    raise ValueError(f"Expected {field} records")
                for row in payload[field]:
                    for key in ("canonical_url", "description_text", "skill_id", "skill_name", "role_name", "title", "location_text"):
                        if key in row and not isinstance(row[key], str):
                            raise ValueError(f"Expected text in {field}.{key}")
        for field in ("provenance", "quality", "evaluation"):
            if payload.get(field) is not None and not isinstance(payload[field], dict):
                raise ValueError(f"Expected {field} object")
        return payload, None
    except (OSError, ValueError, TypeError):
        return None, "The market snapshot could not be read. Select a valid snapshot or rebuild it; the other tools remain available."


def render_methodology(snapshot: dict | None) -> None:
    st.title("Evidence, with its limits in view")
    st.write("Career Radar connects job-posting evidence with explainable analytical tools. It is a portfolio research studio, not a census of Irish employment or a prediction of individual hiring outcomes.")
    with st.container(border=True):
        st.subheader("Three kinds of evidence")
        st.markdown("**Observed:** selected job postings, normalised roles and rule-based skill mentions. A mention does not establish proficiency or importance.\n\n**Self-reported:** skills and evidence supplied for a readiness comparison; these are not independently verified.\n\n**Synthetic:** generated career histories used only to demonstrate analytical methods and scenarios.")
    st.subheader("Source quality and publication")
    st.write("Collection caps, search terms, employer concentration, missing fields and source coverage affect the sample. Unreviewed results are for a private development pilot. The extraction publication gate requires at least 100 reviewed records and 90% precision; passing it does not establish representative market coverage or source reuse permission.")
    if snapshot:
        metadata = snapshot.get("metadata", {})
        provenance = snapshot.get("provenance") or {}
        quality = snapshot.get("quality") or {}
        st.write("Loaded dataset", metadata.get("dataset_label", "Not supplied"))
        st.write("Status", metadata.get("data_status", "unknown"))
        st.write("Collection timestamp", provenance.get("collection_timestamp") or "Not supplied")
        st.write("Snapshot generation timestamp", metadata.get("generated_at", "Not supplied"))
        if quality.get("source_counts"):
            st.write("Source coverage", quality["source_counts"])
        if quality:
            with st.expander("Inspect dataset quality"):
                st.json(quality)
        evaluation = snapshot.get("evaluation")
        if evaluation:
            with st.expander("Inspect extraction evaluation"):
                st.json(evaluation)
        else:
            st.info("No completed extraction evaluation is attached to this snapshot.")
    st.subheader("Your inputs")
    st.write("No accounts are required. Candidate and job-description inputs are used during the session and are not written to the project dataset. Avoid entering personal identifiers or confidential text. Session state is temporary application state, not a secure document vault.")
    st.caption("Sources and calculations should be inspected before making a decision. Alignment scores are not callback probabilities; synthetic salary changes are not observed returns.")


def main() -> None:
    st.set_page_config(page_title="Career Radar · Ireland", page_icon="✳", layout="wide")
    apply_styles()
    st.markdown('<div class="radar-brand">CAREER RADAR / IRELAND</div>', unsafe_allow_html=True)
    options = ["Home", *ROUTES, "Methodology"]
    if st.session_state.get("radar_route") not in options:
        st.session_state["radar_route"] = "Home"
    with st.container(key="radar_nav"):
        route = st.radio("Explore Career Radar", options, key="radar_route", horizontal=True, label_visibility="collapsed")
    snapshot, error = read_snapshot(Path(os.getenv("CAREER_RADAR_SNAPSHOT", str(DEFAULT_SNAPSHOT))))
    if error:
        st.info(error)
    elif not snapshot["metadata"].get("publish_allowed", False):
        st.warning(f"Loaded job sample: {str(snapshot['metadata'].get('data_status', 'unreviewed')).upper()} DATA · Private development pilot. Not approved for public market claims.")
    taxonomy = load_taxonomy(ROOT / "data" / "reference" / "skills.csv")
    if route == "Home":
        home.render(snapshot, taxonomy)
    elif route == "Methodology":
        render_methodology(snapshot)
    else:
        module_name = f"career_radar.ui.{ROUTES[route]}"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name != module_name:
                raise
            st.info("This tool is being integrated. Explore another tool or return to Home.")
        else:
            module.render(snapshot, taxonomy)
    st.markdown('<div class="radar-footer">Dublin Analytics Career Radar · Evidence before inference · Observed and synthetic data kept distinct</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

"""Landing page: four clear entry points, supported by honest data status."""
from __future__ import annotations

import streamlit as st

TOOLS = (
    ("Skill Constellation", "01", "See how skills connect", "Explore skills that appear together across advertised roles. Follow each connection back to its source evidence.", "OBSERVED JOB SAMPLE", "constellation"),
    ("Readiness Studio", "02", "Make your evidence visible", "Compare the skills you can demonstrate with advertised requirements. Explore gaps and practical next steps.", "SELF-REPORTED + OBSERVED", "readiness"),
    ("Career Mobility", "03", "Explore the paths between roles", "Investigate career transitions and salary trajectories in a reproducible simulation. Test scenarios and inspect the assumptions.", "SYNTHETIC SCENARIOS", "mobility"),
    ("JD Diagnostic", "04", "Read between the requirements", "Inspect a job description for skill mentions, unclear requirements and missing information. Every finding has an explanation.", "USER-PROVIDED TEXT", "diagnostic"),
)


def navigate(route: str) -> None:
    st.session_state["radar_route"] = route


def render(snapshot: dict | None, taxonomy: list) -> None:
    st.markdown('<div class="radar-eyebrow">DUBLIN ROOTS. IRELAND-WIDE PERSPECTIVE.</div>', unsafe_allow_html=True)
    st.markdown("""<div class="radar-orbit" aria-hidden="true"><svg viewBox="0 0 190 62" xmlns="http://www.w3.org/2000/svg" role="presentation" focusable="false">
    <g fill="none" stroke="#84aca2" stroke-width="1.3"><path d="M12 43L49 13L91 37L135 9L177 39M12 43L91 37L135 9M49 13L54 54L91 37L140 55L177 39"/></g>
    <g fill="#17675e"><circle cx="12" cy="43" r="4"/><circle cx="49" cy="13" r="5"/><circle cx="91" cy="37" r="7"/><circle cx="177" cy="39" r="4"/><circle cx="54" cy="54" r="3"/><circle cx="140" cy="55" r="3"/></g>
    <circle cx="135" cy="9" r="5" fill="#b8552e"/></svg></div>""", unsafe_allow_html=True)
    st.title("Evidence for your next career move")
    st.markdown('<p class="radar-lede">Understand the skills behind the listings. Examine your evidence. Explore the possibilities—with the assumptions in view.</p>', unsafe_allow_html=True)
    st.caption("Four analytical tools · Traceable job evidence · Explainable methods")
    st.divider()
    st.subheader("Choose your question")
    for row in (TOOLS[:2], TOOLS[2:]):
        for column, (route, number, title, description, label, key) in zip(st.columns(2, gap="large"), row):
            with column:
                with st.container(border=True):
                    st.markdown(f'<div class="radar-number">{number} / {route.upper()}</div>', unsafe_allow_html=True)
                    st.subheader(title)
                    st.write(description)
                    st.markdown(f'<span class="radar-chip">{label}</span>', unsafe_allow_html=True)
                    st.button(f"Open {route} →", key=f"open_{key}", on_click=navigate, args=(route,), width="stretch")
    st.divider()
    st.subheader("Know what you’re looking at")
    if snapshot:
        metadata = snapshot.get("metadata", {})
        market = snapshot.get("market", {})
        provenance = snapshot.get("provenance") or {}
        columns = st.columns(3)
        count = market.get("sample_size")
        columns[0].metric("Postings in loaded sample", str(count) if count is not None else "Not supplied")
        columns[1].metric("Dataset status", str(metadata.get("data_status", "unknown")).capitalize())
        columns[2].metric("Collection time", str(provenance.get("collection_timestamp") or "Not supplied"))
        st.caption(f"Dataset: {metadata.get('dataset_label', 'Not supplied')}. Snapshot generated: {metadata.get('generated_at', 'Not supplied')}. Generation time is not collection time.")
    else:
        st.info("No observed market snapshot is loaded. The diagnostic and synthetic lab remain available; tools explain when market evidence is needed.")
    st.write("Observed listings describe a selected sample, not the whole Irish labour market. Candidate inputs are self-reported; career mobility results are synthetic. None of these tools predicts a callback or a salary outcome.")
    st.button("Explore the methodology", on_click=navigate, args=("Methodology",), key="home_methodology")

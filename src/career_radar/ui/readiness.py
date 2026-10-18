"""Session-scoped Opportunity Readiness Studio, with inspectable assumptions."""

from __future__ import annotations

import hashlib
import json

import pandas as pd
import streamlit as st

from career_radar.normalise import Skill
from career_radar.readiness import assess_readiness, export_analysis, hypothetical_readiness
from career_radar.requirements_model import extract_requirements

PREFIX = "readiness_"
DEMO = "Required skills: SQL and Python.\nPreferred: Tableau.\nDegree requirements and work eligibility must be checked with the employer."


def _reset() -> None:
    for key in list(st.session_state):
        if key.startswith(PREFIX):
            del st.session_state[key]


def _show_summary(result: dict) -> None:
    cols = st.columns(3)
    cols[0].metric("Assessed-weight coverage", "Not available" if result["coverage_pct"] is None else f"{result['coverage_pct']:.1f}%")
    cols[1].metric("Evidence alignment index", "Suppressed" if result["alignment_pct"] is None else f"{result['alignment_pct']:.1f} / 100")
    cols[2].metric("Unassessed weight", f"{result['unassessed_weight']:g} / {result['total_weight']:g}")
    if result["alignment_pct"] is None:
        st.info("An index needs confirmed skill requirements and at least 80% assessed-weight coverage. Unknowns remain visible.")
    st.caption(result["formula"])
    st.caption(result["limitation"])


def render(snapshot: dict | None, taxonomy: list[Skill]) -> None:
    st.header("Opportunity Readiness Studio")
    st.write("Which requirements can you demonstrate, and where is evidence missing?")
    st.caption("Self-reported evidence · session-only · deterministic rules · no account or résumé upload")
    st.button("Clear all readiness inputs and results", key=PREFIX + "clear", on_click=_reset)
    postings = (snapshot or {}).get("postings", [])
    sources = ["Paste a description", "Demonstration description"]
    if postings:
        sources.append("Select a source posting")
    mode = st.radio("Requirement source", sources, key=PREFIX + "source")
    if mode == "Paste a description":
        text = st.text_area("Job description (omit contact details)", height=180, key=PREFIX + "text", max_chars=30000)
    elif mode == "Demonstration description":
        text = DEMO
        st.info("Illustrative requirements for learning the workflow; not a real vacancy.")
        st.text(text)
    else:
        index = st.selectbox("Posting", range(len(postings)), format_func=lambda i: f"{postings[i].get('title', 'Untitled')} · {postings[i].get('employer_name', 'Employer unknown')} · {postings[i].get('location_text', 'Location unknown')}", key=PREFIX + "posting")
        posting = postings[index]
        text = posting.get("description_text", "")
        st.caption(f"Source: {posting.get('canonical_url', 'Not supplied')} · Posted: {posting.get('posted_at') or posting.get('date_posted') or 'Unknown'}")
        with st.expander("Original posting text"):
            st.text(text)
    signature = hashlib.sha256((mode + text).encode()).hexdigest()[:16]
    if st.session_state.get(PREFIX + "signature") != signature:
        for key in list(st.session_state):
            if key.startswith(PREFIX + "item_") or key in {PREFIX + "result", PREFIX + "evidence", PREFIX + "scenario", PREFIX + "whatif", PREFIX + "whatif_note", PREFIX + "download"}:
                del st.session_state[key]
        st.session_state[PREFIX + "signature"] = signature
    st.warning("Skills alignment is not a hiring or callback prediction. Explicit degree, grade, location and work-eligibility conditions are outside this index and are not assessed. Check the original listing; unknown is not failure.")
    if not text.strip():
        st.info("Paste a description, choose a source posting, or try the labelled demonstration.")
        return
    requirements = extract_requirements(text, taxonomy)
    if not requirements:
        st.info("No controlled skill requirements were found. This does not establish that the role has no requirements. Review the original description.")
        return
    st.subheader("Review source requirements")
    st.dataframe(pd.DataFrame([{"Skill": r["skill_name"], "Classification": r["requirement_type"], "Exact phrase": r["source_phrase"], "Context": r["source_text"]} for r in requirements]), hide_index=True, width="stretch")
    st.caption("Rule classifications may be wrong. Uncertain and negated mentions are shown but excluded. Repeated skills count once at the strongest requirement level; contradictory evidence remains conservative.")
    st.subheader("Your evidence matrix")
    st.write("Review each extracted classification against its source context and correct any parsing error before assessment. If the text is unclear, keep it uncertain. For skill requirements, choose an evidence status and describe a concrete project, coursework outcome or experience. Participation alone does not establish proficiency. Do not enter personal contact information.")
    entries = {}
    confirmed_requirements = []
    with st.form(PREFIX + "form"):
        for row in requirements:
            identifier = row["requirement_id"]
            st.markdown(f"**{row['skill_name']} · {row['requirement_type']}**")
            st.text(row["source_text"])
            kinds = ["required", "preferred", "uncertain", "negated"]
            classification = st.selectbox("Confirm or correct requirement classification", kinds, index=kinds.index(row["requirement_type"]), key=PREFIX + "item_" + identifier + "_classification")
            confirmed_requirements.append({**row, "requirement_type": classification, "extracted_requirement_type": row["requirement_type"], "classification_provenance": "user-confirmed", "classification_corrected": classification != row["requirement_type"]})
            status = st.selectbox("Evidence status", ["unknown", "supported", "partial", "missing"], key=PREFIX + "item_" + identifier + "_status")
            note = st.text_input("Concrete evidence note (required for supported / partial)", key=PREFIX + "item_" + identifier + "_note", max_chars=500)
            entries[identifier] = {"status": status, "note": note}
        st.caption("Submitting confirms your reviewed requirement classifications. Uncertain and negated mentions remain outside the index regardless of evidence status.")
        submitted = st.form_submit_button("Assess self-reported evidence")
    if submitted:
        st.session_state[PREFIX + "evidence"] = entries
        st.session_state[PREFIX + "result"] = assess_readiness(confirmed_requirements, entries)
        st.session_state.pop(PREFIX + "scenario", None)
    result = st.session_state.get(PREFIX + "result")
    if not result:
        return
    st.subheader("Confirmed baseline — self-reported, not verified")
    for row in result["rows"]:
        if row.get("issue"):
            st.warning(f"{row['skill_name']}: {row['issue']} Status remains unknown.")
    _show_summary(result)
    st.dataframe(pd.DataFrame([{"Skill": row["skill_name"], "Requirement": row["requirement_type"], "Original extraction": row.get("extracted_requirement_type"), "Classification provenance": row.get("classification_provenance"), "Status": row["status"], "Candidate evidence": row["evidence_note"], "Evidence provenance": row["evidence_provenance"]} for row in result["rows"]]), hide_index=True, width="stretch")
    st.caption("If you edit the form, submit again to replace this baseline. Current results reflect the last submitted evidence.")
    gaps = [row for row in result["rows"] if row["weight"] and row["status"] != "supported"]
    if gaps:
        with st.expander("What if I build evidence for one gap?"):
            st.caption("Hypothetical additions never change your submitted baseline or establish a completed qualification.")
            identifiers = [r["requirement_id"] for r in gaps]
            labels = {r["requirement_id"]: r["skill_name"] + " · " + r["requirement_type"] for r in gaps}
            selected = st.selectbox("Gap", identifiers, format_func=lambda key: labels[key], key=PREFIX + "whatif")
            hypothetical_note = st.text_input("Planned evidence", key=PREFIX + "whatif_note", max_chars=500)
            if st.button("Compare hypothetical evidence", key=PREFIX + "compare"):
                if hypothetical_note.strip():
                    st.session_state[PREFIX + "scenario"] = hypothetical_readiness(result["rows"], st.session_state[PREFIX + "evidence"], selected, hypothetical_note)
                else:
                    st.warning("Describe the planned evidence first.")
            scenario = st.session_state.get(PREFIX + "scenario")
            if scenario:
                baseline_col, scenario_col = st.columns(2)
                with baseline_col:
                    st.write("Submitted baseline — self-reported")
                    _show_summary(result)
                with scenario_col:
                    st.write(scenario["label"])
                    _show_summary(scenario)
                st.caption("Shows the last compared scenario; changes to controls apply after Compare. These are rule-based sensitivity results, not expected hiring outcomes.")
    st.download_button("Download baseline skill analysis (notes omitted)", json.dumps(export_analysis(result), indent=2), file_name="readiness_skill_analysis.json", mime="application/json", key=PREFIX + "download")
    st.caption("Download excludes candidate notes, original advert text, identity and contact fields. Clear all removes inputs, results and hypothetical scenarios from this session; files already downloaded remain on your device.")

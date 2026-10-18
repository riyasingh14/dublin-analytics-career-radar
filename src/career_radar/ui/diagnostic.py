"""Session-only UI for deterministic job-description diagnostics."""
from __future__ import annotations
import difflib
import hashlib
import json
import streamlit as st
from career_radar.diagnostic import analyze_description
from career_radar.normalise import Skill

SAMPLE = """Synthetic demonstration — Junior Data Analyst
Dublin, Ireland. Permanent, hybrid.
You will create weekly reports and explain results to stakeholders.
SQL is required; Python is preferred.
Excellent communication and strong knowledge of Excel.
Three years of experience is preferred.
Salary: competitive salary.
"""

def render(snapshot: dict | None, taxonomy: list[Skill]) -> None:
    st.header("Job Description Diagnostic")
    st.write("Inspect what a description states, what needs clarification, and how requirements are prioritised.")
    st.caption("Session-only text • deterministic rules • no external AI • no employer or hiring-quality rating")
    if st.button("Clear diagnostic session", key="jd_reset"):
        for key in list(st.session_state):
            if key.startswith("jd_") and key != "jd_reset":
                del st.session_state[key]
        st.rerun()
    mode = st.radio("Description source", ["Paste text", "Observed sample", "Synthetic example"], horizontal=True, key="jd_mode")
    initial = ""
    source_label = "User-supplied text; source not verified"
    identity = mode
    if mode == "Observed sample":
        postings = (snapshot or {}).get("postings", [])
        if not postings:
            st.info("No posting descriptions are loaded. Paste a description or explicitly choose the synthetic example.")
            return
        index = st.selectbox("Choose posting", range(len(postings)), format_func=lambda i: f"{postings[i].get('title', 'Untitled')} — {postings[i].get('employer_name', 'Unknown employer')}", key="jd_posting")
        posting = postings[index]
        initial = posting.get("description_text", "")
        identity += str(index)
        source_label = f"Observed source sample • {(snapshot or {}).get('metadata', {}).get('data_status', 'unreviewed')}"
        st.caption(source_label)
        if posting.get("canonical_url"):
            st.caption(f"Source: {posting['canonical_url']}")
    elif mode == "Synthetic example":
        initial = SAMPLE
        source_label = "Synthetic demonstration; no employer or real vacancy"
        st.info(source_label)
    text = st.text_area("Description — avoid personal or confidential information", value=initial, height=240, key="jd_text_" + identity)
    if not text.strip():
        st.info("Paste text to start. Examples are available only when you select them above.")
        return
    if len(text) > 50000:
        st.warning("Please use a description of 50,000 characters or fewer. No text has been truncated or analysed.")
        return
    if mode != "Paste text" and text != initial:
        source_label = "User-modified text based on " + ("an observed posting; source assertions apply only to the original" if mode == "Observed sample" else "a synthetic example")
        st.warning(source_label)
    result = analyze_description(text, taxonomy)
    token = hashlib.sha256(text.encode()).hexdigest()[:16]
    st.caption(result["limitations"])
    st.subheader("Completeness checklist")
    st.dataframe([{"Field": key.replace("_", " "), "Status": row["status"], "Evidence": row["source_phrase"] or "Not stated"} for key, row in result["completeness"].items()], hide_index=True, width="stretch")
    st.caption("Present means a matching disclosure phrase was found; it does not validate the detail. Unknown checks need interpretation.")
    st.subheader("Requirement evidence")
    if result["requirements"]:
        st.dataframe([{"Skill": row["skill_name"], "Designation": row["requirement_type"], "Exact phrase": row["source_phrase"], "Source context": row["source_text"], "Start": row["start"], "End": row["end"]} for row in result["requirements"]], hide_index=True, width="stretch")
    else:
        st.info("No taxonomy skills were found. This does not mean the role has no requirements.")
    st.subheader("Review findings")
    st.caption("Review = possible ambiguity or inconsistency; Not stated = field absent in supplied text. Dismissal preserves the original evidence.")
    reviewed = []
    for item in result["findings"]:
        item_key = f"jd_{token}_{item['finding_id']}"
        with st.expander(f"{item['category']} · {item['severity']} · {item['rule']}"):
            st.write(item["rationale"])
            if item["source_phrase"]:
                st.code(item["source_phrase"], language=None)
                st.caption(f"Exact input span [{item['start']}:{item['end']}]")
            else:
                st.caption(f"Absent field: {item['absent_field']}")
            status = st.selectbox("Your review", ["Unreviewed", "Accepted for clarification", "Dismissed", "Uncertain"], key=item_key + "_status")
            edit = st.text_area("Editable clarification proposal — confirm facts before use", value=item["suggestion"], key=item_key + "_edit")
            if item["source_phrase"]:
                st.code("\n".join(difflib.unified_diff(item["source_phrase"].splitlines(), edit.splitlines(), fromfile="Original phrase", tofile="Clarification proposal", lineterm="")), language="diff")
            st.caption("Original text remains unchanged. Proposals ask for missing facts; they do not assert new salary, benefits or policies.")
            reviewed.append({**item, "human_status": status, "edited_suggestion": edit})
    st.subheader("Export review")
    include_evidence = st.checkbox("Include original text and exact source phrases in the download (check for personal information first)", key="jd_include_evidence")
    report = {"rule_version": result["rule_version"], "scope": source_label, "limitations": result["limitations"], "benchmark": None,
              "completeness": result["completeness"], "requirements": result["requirements"], "findings": reviewed}
    if include_evidence:
        report["original_text"] = text
    else:
        report["completeness"] = {key: {"status": value["status"]} for key, value in result["completeness"].items()}
        report["requirements"] = [{key: value for key, value in row.items() if key not in ("source_text", "source_phrase")} for row in result["requirements"]]
        report["findings"] = [{key: value for key, value in row.items() if key != "source_phrase"} for row in reviewed]
    st.caption("JSON export; original/source text is excluded by default. Review your edited suggestions before sharing. Nothing is saved to the repository.")
    st.download_button("Download diagnostic report", data=json.dumps(report, ensure_ascii=False, indent=2), file_name="description_diagnostic.json", mime="application/json", key="jd_download")

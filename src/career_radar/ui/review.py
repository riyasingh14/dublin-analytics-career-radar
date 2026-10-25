"""Manual extraction review with queue-bound, user-downloaded checkpoints."""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from career_radar.review_workspace import (
    annotate,
    evaluate_workspace,
    export_checkpoint,
    export_review_csv,
    initial_annotations,
    load_queue_csv,
    queue_fingerprint,
    restore_checkpoint,
    review_progress,
)

PREFIX = "private_review_"
MAX_BYTES = 4 * 1024 * 1024
STATUSES = ("unreviewed", "accepted", "rejected", "uncertain")
STATUS_NAMES = {
    "unreviewed": "Unreviewed",
    "accepted": "Accepted — the skill mention is correctly extracted",
    "rejected": "Rejected — the extraction is incorrect",
    "uncertain": "Uncertain — needs further human checking",
}


def _clear() -> None:
    epoch = st.session_state.get(PREFIX + "epoch", 0) + 1
    for key in list(st.session_state):
        if key.startswith(PREFIX):
            del st.session_state[key]
    st.session_state[PREFIX + "epoch"] = epoch
    # Clearing must not immediately reload the configured file on the next rerun.
    st.session_state[PREFIX + "environment_checked"] = True


def _install_queue(data: bytes) -> None:
    queue = load_queue_csv(data)
    st.session_state[PREFIX + "queue"] = queue
    st.session_state[PREFIX + "annotations"] = initial_annotations(queue)
    st.session_state[PREFIX + "fingerprint"] = queue_fingerprint(queue)
    st.session_state[PREFIX + "revision"] = st.session_state.get(PREFIX + "revision", 0) + 1


def _read_local_queue(path: str) -> bytes:
    with Path(path).expanduser().open("rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Review queue exceeds the upload limit")
    return data


def render() -> None:
    st.title("Private extraction review")
    st.caption("Human decisions · session-scoped · separate from the public four-tool demo")
    st.write(
        "Inspect each exact phrase in its source context and record your own decision. "
        "Accepted means the skill mention is correctly extracted; it does not mean "
        "the skill is required or that a candidate can demonstrate it."
    )
    st.info(
        "This workbench never publishes a snapshot or fills in review labels for you. "
        "Files are processed by this Streamlit process; downloads can contain source "
        "excerpts and private review notes. Keep them out of Git and public sharing."
    )
    st.button("Clear session", key=PREFIX + "clear", on_click=_clear)

    if not st.session_state.get(PREFIX + "environment_checked"):
        st.session_state[PREFIX + "environment_checked"] = True
        configured = os.environ.get("CAREER_RADAR_REVIEW_QUEUE", "").strip()
        if configured:
            try:
                _install_queue(_read_local_queue(configured))
            except (OSError, ValueError, TypeError, KeyError):
                st.session_state[PREFIX + "load_error"] = (
                    "The configured queue could not be loaded. Check the file, CSV schema, "
                    "record limits and unique evidence identities."
                )

    epoch = st.session_state.get(PREFIX + "epoch", 0)
    queue = st.session_state.get(PREFIX + "queue")
    with st.expander("Load a queue or resume a checkpoint", expanded=not bool(queue)):
        uploaded = st.file_uploader(
            "Review queue CSV", type=["csv"], key=PREFIX + f"upload_{epoch}",
            help="Maximum 4 MiB and 1,000 records. Only review queue fields are retained.",
        )
        if st.button("Load uploaded queue", disabled=uploaded is None, key=PREFIX + "load"):
            try:
                _install_queue(uploaded.getvalue())
                st.session_state.pop(PREFIX + "load_error", None)
                st.rerun()
            except (ValueError, TypeError, KeyError):
                st.session_state[PREFIX + "load_error"] = (
                    "The queue was rejected. Check the CSV schema, unique record/evidence "
                    "identities, existing labels and file limits. Your current review is unchanged."
                )
        checkpoint = st.file_uploader(
            "Saved checkpoint JSON", type=["json"], key=PREFIX + f"checkpoint_{epoch}",
            help="A checkpoint can resume only the identical source queue; it never supplies a replacement queue.",
        )
        if st.button("Restore checkpoint", disabled=not queue or checkpoint is None, key=PREFIX + "restore"):
            try:
                restored = restore_checkpoint(queue, checkpoint.getvalue())
                st.session_state[PREFIX + "annotations"] = restored
                st.session_state[PREFIX + "revision"] = st.session_state.get(PREFIX + "revision", 0) + 1
                st.session_state[PREFIX + "flash"] = "Checkpoint restored for this queue."
                st.rerun()
            except (ValueError, TypeError, KeyError):
                st.error("Checkpoint rejected: it must be valid and match this queue exactly. Your decisions are unchanged.")
    if st.session_state.get(PREFIX + "load_error"):
        st.error(st.session_state[PREFIX + "load_error"])
    if st.session_state.get(PREFIX + "flash"):
        st.success(st.session_state.pop(PREFIX + "flash"))
    queue = st.session_state.get(PREFIX + "queue")
    if not queue:
        st.info(
            "No review queue is loaded. Upload a prepared extraction-review CSV or configure "
            "CAREER_RADAR_REVIEW_QUEUE with a private local file. No demonstration labels are generated."
        )
        return

    annotations = st.session_state[PREFIX + "annotations"]
    progress = review_progress(queue, annotations)
    evaluation = evaluate_workspace(queue, annotations)
    cols = st.columns(4)
    cols[0].metric("Completed decisions", f"{progress['completed']} / {progress['total']}")
    cols[1].metric("Accepted", progress["accepted"])
    cols[2].metric("Rejected", progress["rejected"])
    cols[3].metric("Uncertain", progress["uncertain"])
    st.progress(progress["completed"] / progress["total"] if progress["total"] else 0)
    st.caption("Only accepted and rejected decisions are completed reviews. Uncertain remains outside precision.")
    with st.expander("Category coverage and queue identity"):
        st.dataframe(
            [{"category": category, **counts} for category, counts in progress["by_category"].items()],
            hide_index=True,
        )
        st.text("Queue SHA-256: " + st.session_state[PREFIX + "fingerprint"])
        st.caption("A checkpoint is bound to the source queue, including its immutable evidence fields.")

    categories = sorted({str(row.get("category", "")) for row in queue})
    filter_cols = st.columns(2)
    category = filter_cols[0].selectbox("Category", ["All categories", *categories], key=PREFIX + "category")
    status = filter_cols[1].selectbox("Review status", ["All statuses", *STATUSES], key=PREFIX + "status")
    filtered = [row for row in queue
                if (category == "All categories" or row.get("category", "") == category)
                and (status == "All statuses" or annotations[str(row["review_id"])]["status"] == status)]
    if not filtered:
        st.info("No records match these filters. Change the filters to continue reviewing.")
    else:
        by_id = {str(row["review_id"]): row for row in filtered}
        identifier = st.selectbox(
            "Evidence record", list(by_id),
            format_func=lambda value: f"{value} · {by_id[value].get('skill_name', '')} · {by_id[value].get('job_title', '')}",
            key=PREFIX + "selected",
        )
        row = by_id[identifier]
        st.subheader("Inspect the evidence")
        st.text("Job: " + row.get("job_title", ""))
        st.text("Employer: " + row.get("employer_name", ""))
        st.text("Source identity: " + row.get("canonical_url", ""))
        st.write("**Exact extracted phrase**")
        st.code(row.get("source_phrase", ""), language=None, wrap_lines=True)
        st.write("**Source context**")
        st.code(row.get("context", ""), language=None, wrap_lines=True)
        st.caption(
            f"Skill: {row.get('skill_name', '')} · Category: {row.get('category', '')} · "
            f"Method: {row.get('extraction_method', '')} · Version: {row.get('extraction_version', '')}"
        )
        st.caption("Check the underlying source if the context is insufficient. Choose uncertain rather than guessing.")
        revision = st.session_state.get(PREFIX + "revision", 0)
        current = annotations[identifier]
        with st.form(key=PREFIX + f"decision_{revision}_{identifier}"):
            decision = st.radio(
                "Your decision", STATUSES, index=STATUSES.index(current["status"]),
                format_func=STATUS_NAMES.__getitem__, key=PREFIX + f"label_{revision}_{identifier}",
            )
            notes = st.text_area(
                "Private review notes", value=current["notes"], max_chars=1000,
                key=PREFIX + f"notes_{revision}_{identifier}",
            )
            saved = st.form_submit_button("Save decision")
        if saved:
            try:
                st.session_state[PREFIX + "annotations"] = annotate(queue, annotations, identifier, decision, notes)
                st.session_state[PREFIX + "revision"] = revision + 1
                st.session_state[PREFIX + "flash"] = "Decision saved."
                st.rerun()
            except (ValueError, TypeError, KeyError):
                st.error("Decision was not saved. Choose a valid status and keep notes within 1,000 characters.")
        st.caption("Save before changing records or filters. Decisions in an unsaved form are not included in exports.")

    st.subheader("Evaluation and private exports")
    reviewed = int(evaluation.get("reviewed_count", 0))
    metrics = st.columns(2)
    metrics[0].metric("Observed extraction precision", f"{float(evaluation['precision_pct']):.1f}%" if reviewed else "Not available")
    interval = evaluation.get("precision_95_ci_pct", [0, 0])
    metrics[1].metric("95% Wilson interval", f"{interval[0]:.1f}%–{interval[1]:.1f}%" if reviewed else "Not available")
    st.caption(f"Denominator: {reviewed} accepted/rejected records. Unknown and uncertain decisions are excluded, not treated as errors.")
    st.caption(str(evaluation.get("sampling_limitation", "")))
    if evaluation.get("publication_threshold_met"):
        st.success("The count, precision and coverage checks are met. A snapshot must still verify this review against its actual source inputs. Source/display permission remains separate; this app publishes nothing.")
    else:
        st.info("The applicable extraction-review threshold has not been met. This is a private review, not publication approval.")
    for reason in evaluation.get("gate_reasons", []):
        st.caption(str(reason))
    downloads = st.columns(3)
    downloads[0].download_button("Download review CSV", export_review_csv(queue, annotations), "extraction_review.csv", "text/csv", key=PREFIX + "csv")
    downloads[1].download_button("Download checkpoint", export_checkpoint(queue, annotations), "review_checkpoint.json", "application/json", key=PREFIX + "checkpoint_download")
    downloads[2].download_button("Download evaluation", json.dumps(evaluation, indent=2).encode("utf-8"), "extraction_evaluation.json", "application/json", key=PREFIX + "evaluation")
    st.caption("Downloads are private review artefacts. The CSV includes source excerpts and notes; the checkpoint includes decisions and notes. Nothing overwrites the original queue.")

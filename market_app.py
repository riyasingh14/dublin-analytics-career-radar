"""Streamlit web experience for Dublin Analytics Career Radar."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from career_radar.analytics import load_proof_recommendations, recommend_proof_of_work
from career_radar.normalise import ROLE_RULES


ROOT = Path(__file__).resolve().parent
DEFAULT_SNAPSHOT = ROOT / "data" / "processed" / "market_snapshot.json"
TAXONOMY_PATH = ROOT / "data" / "reference" / "skills.csv"


@st.cache_data
def load_snapshot(path: str, modified_ns: int) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@st.cache_data
def load_taxonomy() -> pd.DataFrame:
    return pd.read_csv(TAXONOMY_PATH)


def main() -> None:
    st.set_page_config(
        page_title="Dublin Analytics Career Radar",
        page_icon="📡",
        layout="wide",
    )
    st.title("Dublin Analytics Career Radar")
    st.caption(
        "Evidence-backed tech career intelligence for Ireland, with Dublin shown separately."
    )

    snapshot_path = Path(os.getenv("CAREER_RADAR_SNAPSHOT", str(DEFAULT_SNAPSHOT)))
    if not snapshot_path.exists():
        st.info(
            "No market snapshot is loaded yet. Connect an authorised source, run the "
            "ingestion workflow, and build a labelled snapshot to activate the dashboard."
        )
        st.code(
            "PYTHONPATH=src python -m career_radar.build_snapshot "
            "--jobs ... --evidence ... --dataset-label ... --data-status unreviewed"
        )
        st.stop()

    try:
        snapshot = load_snapshot(str(snapshot_path), snapshot_path.stat().st_mtime_ns)
    except (OSError, ValueError):
        st.error("The market snapshot could not be read. Rebuild it or select a valid snapshot.")
        st.stop()
    metadata = snapshot["metadata"]
    market = snapshot["market"]
    quality = snapshot.get("quality", {})
    evaluation = snapshot.get("evaluation") or {}
    provenance = snapshot.get("provenance") or {}
    if not metadata["publish_allowed"]:
        st.warning(
            f"{str(metadata['data_status']).upper()} DATA — not approved for public market claims. "
            "Use this view only for development and validation."
        )

    st.caption(
        f"Dataset: {metadata['dataset_label']} · Generated: {metadata['generated_at']} · "
        f"Status: {metadata['data_status']}"
    )
    st.caption(str(metadata["disclosure"]))
    st.caption(
        f"Source collection time: {provenance.get('collection_timestamp') or 'Not supplied'} · "
        f"Source count: {len(quality.get('source_counts', {}))} · "
        "Rule-based extraction; generated time is not source collection time."
    )
    selected_market_geography = "All locations"
    if snapshot.get("geography_markets"):
        selected_market_geography = st.selectbox(
            "Market geography", ["All locations", *sorted(snapshot["geography_markets"])]
        )
        if selected_market_geography != "All locations":
            market = snapshot["geography_markets"][selected_market_geography]

    overview_tab, role_tab, evidence_tab, planner_tab, method_tab = st.tabs(
        ["Market overview", "Role comparison", "Skills evidence", "Proof-of-work planner", "Methodology"]
    )

    with overview_tab:
        total_jobs = int(market["sample_size"])
        roles = market["role_counts"]
        patterns = market["work_pattern_counts"]
        metric_cols = st.columns(3)
        metric_cols[0].metric("Postings in this sample", total_jobs)
        metric_cols[1].metric("Target role groups", sum(role in ROLE_RULES for role in roles))
        metric_cols[2].metric("Skills observed", len(market["top_skills"]))

        st.subheader("Skills appearing in this sample")
        skills_df = pd.DataFrame(market["top_skills"])
        if not skills_df.empty:
            st.bar_chart(
                skills_df.head(15).set_index("skill_name")["sample_share_pct"],
                x_label="Skill",
                y_label="Share of sample postings (%)",
            )
            st.dataframe(
                skills_df.rename(
                    columns={
                        "skill_name": "Skill",
                        "job_count": "Postings",
                        "sample_share_pct": "Sample share (%)",
                    }
                )[["Skill", "Postings", "Sample share (%)"]],
                hide_index=True,
                width="stretch",
            )

        chart_cols = st.columns(2)
        chart_cols[0].subheader("Role coverage")
        chart_cols[0].bar_chart(pd.Series(roles, name="Postings"))
        chart_cols[1].subheader("Work pattern")
        chart_cols[1].bar_chart(pd.Series(patterns, name="Postings"))
        if market.get("geography_counts"):
            st.subheader("Geographic coverage")
            st.bar_chart(pd.Series(market["geography_counts"], name="Postings"))
        st.caption(
            "Search caps and selected titles shape this sample. Role counts are not estimates "
            "of each role's share of Ireland's tech job market."
        )

    with role_tab:
        available_roles = sorted(role for role in market["role_skills"] if role in ROLE_RULES)
        if available_roles:
            selected_role = st.selectbox("Compare skills for", available_roles)
            role_df = pd.DataFrame(market["role_skills"][selected_role])
            st.dataframe(
                role_df.rename(
                    columns={
                        "skill_name": "Skill",
                        "job_count": "Role postings",
                        "role_share_pct": "Role sample share (%)",
                    }
                )[["Skill", "Role postings", "Role sample share (%)"]],
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("No classified target roles are available in this snapshot.")

    with evidence_tab:
        st.subheader("Trace a skill to its source")
        st.caption("Matched phrases are rule-based evidence of a mention and still require human review.")
        evidence_records = snapshot.get("evidence", [])
        if evidence_records:
            evidence_df = pd.DataFrame(evidence_records)
            if selected_market_geography != "All locations" and "geography" in evidence_df.columns:
                evidence_df = evidence_df[evidence_df["geography"] == selected_market_geography]
            selected_skill = st.selectbox("Skill evidence", sorted(evidence_df["skill_name"].unique()))
            selected_evidence_role = st.selectbox(
                "Evidence role", ["All roles", *sorted(evidence_df["role_name"].unique())]
            )
            filtered = evidence_df[evidence_df["skill_name"] == selected_skill]
            if selected_evidence_role != "All roles":
                filtered = filtered[filtered["role_name"] == selected_evidence_role]
            if "geography" in evidence_df.columns:
                selected_geography = st.selectbox(
                    "Evidence geography", ["All locations", *sorted(evidence_df["geography"].unique())]
                )
                if selected_geography != "All locations":
                    filtered = filtered[filtered["geography"] == selected_geography]
            st.write(f"{filtered['canonical_url'].nunique()} source postings in this selection")
            st.dataframe(
                filtered[["skill_name", "source_phrase", "title", "employer_name", "role_name",
                          "canonical_url", "extraction_method", "extraction_version"]],
                hide_index=True,
                width="stretch",
                column_config={"canonical_url": st.column_config.LinkColumn("Source job")},
            )
        else:
            st.info("Rebuild this snapshot to include source-linked skill evidence.")

    with planner_tab:
        st.subheader("Turn a market gap into credible evidence")
        st.write(
            "Choose a target role and the skills you can already demonstrate. The planner "
            "prioritises missing skills using only this labelled market sample."
        )
        taxonomy = load_taxonomy()
        skill_labels = dict(zip(taxonomy["skill_name"], taxonomy["skill_id"]))
        target_roles = sorted(role for role in market["role_skills"] if role in ROLE_RULES)
        if target_roles:
            target_role = st.selectbox("Target role", target_roles, key="planner_role")
            selected_skill_names = st.multiselect(
                "Skills you can currently demonstrate",
                options=sorted(skill_labels),
            )
            current_ids = {skill_labels[name] for name in selected_skill_names}
            recommendations = recommend_proof_of_work(
                market,
                target_role,
                current_ids,
                load_proof_recommendations(TAXONOMY_PATH),
            )
            if recommendations:
                for index, recommendation in enumerate(recommendations, start=1):
                    with st.container(border=True):
                        st.markdown(f"**{index}. {recommendation['skill_name']}**")
                        st.write(recommendation["reason"])
                        st.markdown(f"**Build this evidence:** {recommendation['proof_of_work']}")
            else:
                st.success("No uncovered skills were found for this role in the current sample.")
        else:
            st.info("No target-role evidence is available for recommendations in this sample.")

    with method_tab:
        st.subheader("Data quality and extraction evaluation")
        st.caption("Quality and review statistics below cover the full imported dataset.")
        if quality.get("source_counts"):
            st.write("Source coverage", quality["source_counts"])
        if provenance.get("extraction_versions"):
            st.caption("Extraction versions: " + ", ".join(provenance["extraction_versions"]))
        if quality.get("role_counts", {}).get("Unclassified", 0):
            st.info(
                f"{quality['role_counts']['Unclassified']} postings have no target-role classification. "
                "They remain in sample-wide counts and are excluded from role recommendations."
            )
        if quality:
            quality_cols = st.columns(4)
            quality_cols[0].metric("Sample jobs", int(quality.get("sample_size", 0)))
            quality_cols[1].metric(
                "Classified roles", f"{float(quality.get('classified_role_pct', 0)):.1f}%"
            )
            quality_cols[2].metric(
                "Jobs with skill evidence",
                f"{float(quality.get('jobs_with_skill_evidence_pct', 0)):.1f}%",
            )
            quality_cols[3].metric(
                "Largest employer share",
                f"{float(quality.get('top_employer_share_pct', 0)):.1f}%",
            )
        if evaluation:
            interval = evaluation.get("precision_95_ci_pct", ["—", "—"])
            st.write(
                f"Human review: **{evaluation.get('reviewed_count', 0)} records** · "
                f"precision **{float(evaluation.get('precision_pct', 0)):.1f}%** · "
                f"95% interval **{interval[0]}–{interval[1]}%**"
            )
            if evaluation.get("publication_threshold_met"):
                st.success("The documented human-review threshold has been met.")
            else:
                st.warning("The documented human-review threshold has not been met.")
        else:
            st.info("No completed human extraction evaluation is attached to this snapshot.")

        st.subheader("How to interpret this product")
        st.markdown(
            """
            - This is sample-based career intelligence, not a complete census of Irish tech jobs.
            - Every skill is linked to source evidence, extraction method, version, and confidence.
            - Public claims require a manually reviewed, validated snapshot.
            - The MVP stores no candidate account or CV.
            - Recommendations support career planning; they do not predict hiring outcomes.
            """
        )


if __name__ == "__main__":
    main()

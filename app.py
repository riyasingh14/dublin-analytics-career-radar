"""Streamlit web experience for Dublin Analytics Career Radar."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from career_radar.analytics import load_proof_recommendations, recommend_proof_of_work


ROOT = Path(__file__).resolve().parent
DEFAULT_SNAPSHOT = ROOT / "data" / "processed" / "market_snapshot.json"
TAXONOMY_PATH = ROOT / "data" / "reference" / "skills.csv"


@st.cache_data
def load_snapshot(path: str) -> dict[str, object]:
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
        "AI-assisted, evidence-backed skills intelligence for Dublin analytics careers."
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

    snapshot = load_snapshot(str(snapshot_path))
    metadata = snapshot["metadata"]
    market = snapshot["market"]
    quality = snapshot.get("quality", {})
    evaluation = snapshot.get("evaluation") or {}
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

    overview_tab, role_tab, planner_tab, method_tab = st.tabs(
        ["Market overview", "Role comparison", "Proof-of-work planner", "Methodology"]
    )

    with overview_tab:
        total_jobs = int(market["sample_size"])
        roles = market["role_counts"]
        patterns = market["work_pattern_counts"]
        metric_cols = st.columns(3)
        metric_cols[0].metric("Postings in this sample", total_jobs)
        metric_cols[1].metric("Target role groups", len(roles))
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

    with role_tab:
        available_roles = sorted(market["role_skills"])
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

    with planner_tab:
        st.subheader("Turn a market gap into credible evidence")
        st.write(
            "Choose a target role and the skills you can already demonstrate. The planner "
            "prioritises missing skills using only this labelled market sample."
        )
        taxonomy = load_taxonomy()
        skill_labels = dict(zip(taxonomy["skill_name"], taxonomy["skill_id"]))
        target_roles = sorted(market["role_skills"])
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

    with method_tab:
        st.subheader("Data quality and extraction evaluation")
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
            - This is sample-based career intelligence, not a complete census of Dublin jobs.
            - Every skill is linked to source evidence, extraction method, version, and confidence.
            - Public claims require a manually reviewed, validated snapshot.
            - The MVP stores no candidate account or CV.
            - Recommendations support career planning; they do not predict hiring outcomes.
            """
        )


if __name__ == "__main__":
    main()

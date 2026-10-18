"""Interactive, bounded Skill Constellation views with source evidence."""
from __future__ import annotations

import csv
import io
import math

import plotly.graph_objects as go
import streamlit as st

from career_radar.constellation import build_constellation, pair_evidence, safe_source_url
from career_radar.normalise import Skill, geography_group
from career_radar.demo import constellation_demo

PALETTE = ("#64d9cf", "#a7b7ff", "#f5c77e", "#ef9baa", "#9cdb9a", "#bfa1f2", "#81c9ed")


def _csv_bytes(rows: list[dict]) -> bytes:
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _network(result: dict, taxonomy: list[Skill], selected: str | None, metric: str) -> go.Figure:
    """Fixed taxonomy-wide circular positions keep node locations stable on filters."""
    all_ids = sorted({skill.skill_id for skill in taxonomy} | {node["skill_id"] for node in result["nodes"]})
    positions = {skill: (math.cos(2 * math.pi * i / len(all_ids)), math.sin(2 * math.pi * i / len(all_ids)))
                 for i, skill in enumerate(all_ids)}
    if selected:
        adjacent = sorted((pair for pair in result["eligible_pairs"] if selected in {pair["skill_a"], pair["skill_b"]}),
                          key=lambda pair: (-pair[metric], pair["skill_a"], pair["skill_b"]))
        neighbors = [pair["skill_b"] if pair["skill_a"] == selected else pair["skill_a"] for pair in adjacent[:39]]
        visible = {selected, *neighbors}
        nodes = [node for node in result["nodes"] if node["skill_id"] in visible]
    else:
        nodes = result["nodes"][:40]
        visible = {node["skill_id"] for node in nodes}
    edges = [pair for pair in result["eligible_pairs"] if {pair["skill_a"], pair["skill_b"]} <= visible
             and (selected is None or selected in {pair["skill_a"], pair["skill_b"]})]
    edges = sorted(edges, key=lambda pair: (-pair[metric], pair["skill_a"], pair["skill_b"]))[:80]
    # Hide isolated nodes in the graph; the accessible skill table retains them.
    connected = {pair[key] for pair in edges for key in ("skill_a", "skill_b")}
    nodes = [node for node in nodes if node["skill_id"] in connected]
    fig = go.Figure()
    for pair in edges:
        a, b = positions[pair["skill_a"]], positions[pair["skill_b"]]
        fig.add_trace(go.Scatter(x=[a[0], b[0]], y=[a[1], b[1]], mode="lines",
                                 line={"color": "rgba(110,150,180,.35)", "width": 1 + 3 * pair["support"]},
                                 hoverinfo="text", text=f"{pair['skill_a']} + {pair['skill_b']} · {pair['pair_count']} postings · {metric}: {pair[metric]:.3f}",
                                 showlegend=False))
    categories = {skill.skill_id: skill.category for skill in taxonomy}
    category_names = sorted(set(categories.values()) | {"Other"})
    for category in category_names:
        subset = [node for node in nodes if categories.get(node["skill_id"], "Other") == category]
        if not subset:
            continue
        fig.add_trace(go.Scatter(
            x=[positions[node["skill_id"]][0] for node in subset],
            y=[positions[node["skill_id"]][1] for node in subset], mode="markers+text", name=category,
            text=[node["skill_name"] for node in subset], textposition="top center",
            customdata=[[node["job_count"], node["sample_share"]] for node in subset],
            hovertemplate="%{text}<br>%{customdata[0]} unique postings<br>Sample share %{customdata[1]:.1%}<extra></extra>",
            marker={"size": [12 + 28 * math.sqrt(node["sample_share"]) for node in subset],
                    "color": PALETTE[category_names.index(category) % len(PALETTE)],
                    "line": {"width": [3 if node["skill_id"] == selected else 1 for node in subset], "color": "#ffffff"}},
        ))
    fig.update_layout(height=550, margin={"l": 20, "r": 20, "t": 30, "b": 20},
                      xaxis={"visible": False}, yaxis={"visible": False, "scaleanchor": "x"},
                      legend={"orientation": "h"}, dragmode="pan")
    return fig


def render(snapshot: dict | None, taxonomy: list[Skill]) -> None:
    st.header("Skill Constellation")
    st.write("Explore skills mentioned together in the same posting, then inspect the exact source phrases.")
    if not snapshot:
        st.info("No job snapshot is loaded. Import a reviewed source or build a labelled fixture snapshot to explore skills.")
        if st.toggle("Try a synthetic constellation demonstration", key="sc_demo"):
            snapshot = constellation_demo(taxonomy)
            st.warning("Synthetic demonstration: all 30 example postings and employers are fictional. These are not Irish market observations.")
        else:
            return
    if "postings" not in snapshot:
        st.warning("This snapshot predates posting-level records. Rebuild it to include jobs with no extracted skills and obtain valid filtered denominators.")
        return
    metadata = snapshot.get("metadata", {})
    st.caption(f"Dataset: {metadata.get('dataset_label', 'unknown')} · Status: {metadata.get('data_status', 'unknown')} · Built: {metadata.get('generated_at', 'not supplied')}")
    if metadata.get("data_status") != "validated" or not metadata.get("publish_allowed"):
        st.warning("Exploratory sample only. This dataset is not cleared for public market claims.")
    postings = snapshot["postings"]
    roles = sorted({row.get("role_name") or "Unclassified" for row in postings})
    geographies = sorted({row.get("geography") or geography_group(row.get("location_text", "")) for row in postings})
    left, right = st.columns(2)
    role = left.selectbox("Role sample", ["All roles", *roles], key="sc_role")
    geography = right.selectbox("Geography sample", ["All available locations", "Ireland", *geographies], key="sc_geography")
    with st.expander("Display guards and metric definitions"):
        st.caption("Display thresholds are exploratory product guards, not significance tests. Lowering them does not make sparse evidence reliable.")
        min_sample = st.number_input("Minimum postings for network", min_value=1, value=20, key="sc_sample")
        min_count = st.number_input("Minimum co-mentions for an edge", min_value=1, value=5, key="sc_count")
        st.markdown("**N** = all unique postings in the selected sample, including those with no extracted skills. **n(A)** and **n(A,B)** count unique postings, never word occurrences.")
        st.code("Skill share = n(A) / N\nPair support = n(A,B) / N\nJaccard = n(A,B) / (n(A) + n(B) − n(A,B))\nLift = n(A,B) × N / (n(A) × n(B))")
        st.caption("Zero denominators return zero. Co-mention is not causation, a hiring outcome, or a measure of complete market demand.")
    kwargs = {"role": None if role == "All roles" else role,
              "geography": None if geography == "All available locations" else geography,
              "min_sample_size": int(min_sample), "min_pair_count": int(min_count)}
    result = build_constellation(snapshot, **kwargs)
    a, b, c = st.columns(3)
    a.metric("Unique postings (N)", result["sample_size"])
    b.metric("Postings with skills", result["jobs_with_skills"])
    c.metric("Distinct skills", len(result["nodes"]))
    st.caption("Coverage reflects the selected sources, role classification and extraction rules. Missing skill evidence is not proof that a role does not require that skill.")
    if not result["sample_size"]:
        st.info("No postings match this selection. Broaden the role or geography.")
        return
    labels = {node["skill_id"]: node["skill_name"] for node in result["nodes"]}
    if not labels:
        st.info("These postings have no extracted skills. They remain in the denominator; no connections can be shown.")
        return
    selected = st.selectbox("Focus skill", [None, *sorted(labels)], format_func=lambda skill: "All skills" if skill is None else labels[skill], key="sc_skill")
    metric = st.selectbox("Compare connections by", ["support", "jaccard", "lift"], key="sc_metric")
    if not result["network_eligible"]:
        st.info(f"Sparse sample: at least {min_sample} postings are required for the network. Counts below remain descriptive; no connection ranking is shown.")
    elif not result["eligible_pairs"]:
        st.info(f"No pair has at least {min_count} co-mentions. Inspect descriptive counts or broaden the sample.")
    elif selected and not any(selected in {pair["skill_a"], pair["skill_b"]} for pair in result["eligible_pairs"]):
        st.info("The selected skill has no connections meeting the display guards. Its descriptive counts remain available below.")
    else:
        st.plotly_chart(_network(result, taxonomy, selected, metric), width="stretch")
        st.caption("Fixed skill positions · Node size: posting count · At most 40 nodes and 80 edges · Select a pair below for evidence. Full counts remain in the tables.")
    skill_tab, pair_tab, heat_tab, compare_tab = st.tabs(["Skill counts", "Pair metrics", "Co-mention heatmap", "Compare roles"])
    with skill_tab:
        st.dataframe(result["nodes"], width="stretch", hide_index=True)
    with pair_tab:
        pairs = [pair for pair in result["pairs"] if selected is None or selected in {pair["skill_a"], pair["skill_b"]}]
        if not result["network_eligible"]:
            pairs = sorted(pairs, key=lambda pair: (pair["skill_a"], pair["skill_b"]))
        else:
            pairs = sorted(pairs, key=lambda pair: (-pair[metric], pair["skill_a"], pair["skill_b"]))
        st.dataframe(pairs, width="stretch", hide_index=True)
        st.download_button("Export pair metrics", _csv_bytes([{**pair, "sample_size": result["sample_size"], "role_filter": role, "geography_filter": geography} for pair in pairs]), "skill_pair_metrics.csv", "text/csv")
        st.caption(f"All pair metrics use N={result['sample_size']}. Pair table includes counts below the network threshold.")
    with heat_tab:
        ids = sorted(labels)[:20] if not result["network_eligible"] else [node["skill_id"] for node in result["nodes"][:20]]
        if selected and selected not in ids:
            ids = [selected, *ids[:19]]
        pair_counts = {tuple(sorted((pair["skill_a"], pair["skill_b"]))): pair["pair_count"] for pair in result["pairs"]}
        counts = {node["skill_id"]: node["job_count"] for node in result["nodes"]}
        z = [[counts[a] if a == b else pair_counts.get(tuple(sorted((a, b))), 0) for b in ids] for a in ids]
        st.plotly_chart(go.Figure(go.Heatmap(z=z, x=[labels[i] for i in ids], y=[labels[i] for i in ids], colorscale="Teal", hovertemplate="%{y} / %{x}: %{z} postings<extra></extra>")), width="stretch")
        st.caption("Up to 20 skills. Cells show unique-posting co-mentions; diagonal shows each skill's posting count.")
    with compare_tab:
        comparison = st.selectbox("Compare against role", ["Choose a role", *roles], key="sc_compare")
        if comparison != "Choose a role":
            other = build_constellation(snapshot, **{**kwargs, "role": comparison})
            other_nodes = {node["skill_id"]: node for node in other["nodes"]}
            first_nodes = {node["skill_id"]: node for node in result["nodes"]}
            st.caption(f"Selected sample N={result['sample_size']}; {comparison} N={other['sample_size']}. Geography is held constant. Small samples remain descriptive.")
            st.dataframe([{"skill": labels.get(skill, other_nodes.get(skill, {}).get("skill_name", skill)),
                           "selected_count": first_nodes.get(skill, {}).get("job_count", 0),
                           "selected_share": first_nodes.get(skill, {}).get("sample_share", 0),
                           "comparison_count": other_nodes.get(skill, {}).get("job_count", 0),
                           "comparison_share": other_nodes.get(skill, {}).get("sample_share", 0)}
                          for skill in sorted(set(first_nodes) | set(other_nodes))], hide_index=True, width="stretch")
    st.subheader("Inspect a connection")
    available_pairs = [pair for pair in result["pairs"] if selected is None or selected in {pair["skill_a"], pair["skill_b"]}]
    if not result["network_eligible"]:
        available_pairs.sort(key=lambda pair: (pair["skill_a"], pair["skill_b"]))
    if not available_pairs:
        st.info("No co-mentions are available for this skill and sample.")
        return
    pair = st.selectbox("Source-backed pair", available_pairs,
                        format_func=lambda item: f"{labels[item['skill_a']]} + {labels[item['skill_b']]} · {item['pair_count']} postings", key="sc_pair")
    sources = pair_evidence(result, pair["skill_a"], pair["skill_b"])
    st.caption(f"{len(sources)} unique postings support this pair. Collection time: {snapshot.get('provenance', {}).get('collection_timestamp') or 'not supplied'}.")
    for source in sources[:30]:
        posting = source["posting"]
        with st.expander(f"{posting['title']} · {posting['employer_name']}"):
            st.text(f"{posting['location_text']} · {posting['source_name']} · Posted: {posting['posted_at'] or 'not supplied'}")
            url = safe_source_url(posting["canonical_url"])
            if url:
                st.link_button("Open source posting", url)
            for skill, phrases in source["skills"].items():
                st.write(labels[skill])
                for phrase in phrases:
                    st.text(phrase["source_phrase"])
                    st.caption(f"Method: {phrase['extraction_method']} · Version: {phrase['extraction_version']}")
    if len(sources) > 30:
        st.caption("Showing the first 30 supporting postings.")

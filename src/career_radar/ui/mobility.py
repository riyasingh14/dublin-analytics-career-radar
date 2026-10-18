"""Streamlit explorer for the independent synthetic Career Mobility Lab."""
from __future__ import annotations

import json
import math

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
import streamlit as st

from career_radar.mobility import (
    LABEL, LEVELS, MIN_PAIRS, OCCUPATIONS, VERSION, Scenario, derive_transitions,
    generate_histories, metadata, salary_metrics,
)


@st.cache_data(show_spinner=False, max_entries=6)
def _dataset(scenario: Scenario):
    spells = generate_histories(scenario)
    return spells, derive_transitions(spells)


def _title(text):
    return f"{text}<br><sup>{LABEL} · {VERSION}</sup>"


def _figure(fig, title):
    fig.update_layout(title=_title(title), height=510, margin=dict(l=15, r=15, b=30, t=85))
    return fig


def _flows(rows):
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    result = []
    for (origin, destination), group in frame.groupby(["origin_state", "destination_state"], sort=True):
        metrics = salary_metrics(group.to_dict("records"))
        result.append({"origin": origin, "destination": destination, **metrics,
                       "data_label": LABEL, "generator_version": VERSION})
    return sorted(result, key=lambda row: (-row["events"], row["origin"], row["destination"]))


def _radial(flows):
    # Fixed complete state universe keeps positions unchanged under all filters.
    nodes = sorted([f"{o} / {l}" for o in OCCUPATIONS for l in LEVELS] + ["Career break / Not employed"])
    positions = {n: (math.cos(i * 2 * math.pi / len(nodes)), math.sin(i * 2 * math.pi / len(nodes)))
                 for i, n in enumerate(nodes)}
    fig = go.Figure()
    active = set()
    scale = [[0., "#D55E00"], [.5, "#eeeeee"], [1., "#0072B2"]]
    for row in flows:
        a, b = row["origin"], row["destination"]
        active.update((a, b))
        x1, y1 = positions[a]
        x2, y2 = positions[b]
        if a == b:
            xs = [x1 + .075 * math.cos(i * math.pi / 15) for i in range(31)]
            ys = [y1 + .075 + .075 * math.sin(i * math.pi / 15) for i in range(31)]
        else:
            xs, ys = [x1, x2], [y1, y2]
        value = row["median_individual_pct_change"]
        color = "#969696" if not row["comparison_available"] else sample_colorscale(scale, [(max(-20., min(20., value)) + 20) / 40])[0]
        salary = f"{value:.1f}%" if row["comparison_available"] else f"suppressed (<{MIN_PAIRS} valid pairs)"
        text = (f"{a} → {b}<br>Events: {row['events']} · people: {row['people']}"
                f"<br>Valid pairs: {row['valid_pairs']}<br>Median individual change: {salary}"
                f"<br>{LABEL} · {VERSION}")
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=min(12, 1 + math.sqrt(row["events"]))),
                                 text=text, hoverinfo="text", showlegend=False))
    fig.add_trace(go.Scatter(x=[None, None], y=[None, None], mode="markers", showlegend=False,
        marker=dict(color=[-20, 20], cmin=-20, cmax=20, colorscale=scale,
                    showscale=True, colorbar=dict(title="Median change (%)")), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color="#969696", width=4), name="Insufficient pairs", hoverinfo="skip"))
    visible = [n for n in nodes if n in active]
    fig.add_trace(go.Scatter(x=[positions[n][0] for n in visible], y=[positions[n][1] for n in visible],
                             text=visible, mode="markers", marker=dict(size=12, color="#4a5568"),
                             hovertemplate="%{text}<br>" + LABEL + " · " + VERSION + "<extra></extra>", showlegend=False))
    fig.update_xaxes(visible=False, range=[-1.2, 1.2])
    fig.update_yaxes(visible=False, scaleanchor="x", range=[-1.2, 1.2])
    return _figure(fig, "Career-state network · width = event count; colour = median-change sign")


def _sankey(flows):
    origins = sorted({r["origin"] for r in flows})
    destinations = sorted({r["destination"] for r in flows})
    nodes = origins + destinations
    fig = go.Figure(go.Sankey(
        node=dict(label=[f"From: {n}" for n in origins] + [f"To: {n}" for n in destinations],
                  customdata=[LABEL + " · " + VERSION] * len(nodes),
                  hovertemplate="%{label}<br>%{customdata}<extra></extra>"),
        link=dict(source=[origins.index(r["origin"]) for r in flows],
                  target=[len(origins) + destinations.index(r["destination"]) for r in flows],
                  value=[r["events"] for r in flows], customdata=[LABEL + " · " + VERSION] * len(flows),
                  hovertemplate="%{source.label} → %{target.label}<br>Events: %{value}<br>%{customdata}<extra></extra>")))
    return _figure(fig, "Career-state flows · event counts")


def _filter(rows, origin, destination, level, industry, destination_level, destination_industry, geography, experience, period, category):
    return [r for r in rows if (origin == "All" or r["origin"] == origin)
            and (destination == "All" or r["destination"] == destination)
            and (level == "All" or r["origin_seniority"] == level)
            and (industry == "All" or r["origin_industry"] == industry)
            and (destination_level == "All" or r["destination_seniority"] == destination_level)
            and (destination_industry == "All" or r["destination_industry"] == destination_industry)
            and (geography == "All" or r["geography"] == geography)
            and experience[0] <= r["experience_years"] <= experience[1]
            and period[0] <= int(r["date"][:4]) <= period[1]
            and (category == "All" or r["category"] == category)]


def render(snapshot=None, taxonomy=None) -> None:
    st.header("Career Mobility Lab")
    st.warning(LABEL)
    st.write("Explore how disclosed assumptions shape career trajectories. These scenarios do not estimate real salaries, transition probabilities or causal effects.")
    with st.expander("Scenario assumptions and data dictionary", expanded=False):
        st.write("Annual full-time-equivalent base pay in EUR; no inflation adjustment, bonuses or benefits. Each person contributes one non-overlapping annual observation spell, including unchanged jobs. Annual gaps are explicit career breaks, with no salary pair.")
        st.write("Initial pay = €32,000 + €15,000 × level + €900 × experience + a seeded integer offset (-€4,000 to €6,999). Annual noise is selected from 0, 0, -12, -6, -3, 2, 4, 8 percentage points. Employer-change probability 24%; occupation-change 12%; promotion 14% below Lead; break 4.5%, with no consecutive breaks. These are illustrative assumptions, not calibrated Irish rates.")
        st.write("Employer industry is fixed by synthetic employer ID. Experience grows only during employed years; geography is fixed per person. Break/return flags are excluded from employer/promotion groups. Salary has an €18,000 floor. Weights are per transition, not per independent person.")
        st.write("Identifiers: person_id groups a history; spell_id identifies an annual interval [start_date, end_date); transition_id links adjacent spells. Occupation describes work; industry describes the employer sector; seniority is Junior/Mid/Senior/Lead. All records carry a synthetic label and generator version.")
    controls = st.columns(3)
    people = controls[0].selectbox("Synthetic people", [500, 1000, 5000], key="mob_people")
    seed = controls[1].number_input("Scenario seed", min_value=0, max_value=999999, value=42, key="mob_seed")
    years = controls[2].slider("History years", 3, 8, 5, key="mob_years")
    st.caption("Baseline assumptions: employer change +4, promotion +8, occupation change +2 percentage points, added to the annual noise shock. Adjusted results reflect these inputs.")
    controls = st.columns(3)
    employer = controls[0].slider("Employer-change assumption (percentage points)", -15., 20., 4., key="mob_emp")
    promotion = controls[1].slider("Promotion assumption (percentage points)", -15., 20., 8., key="mob_prom")
    role = controls[2].slider("Occupation-change assumption (percentage points)", -15., 20., 2., key="mob_role")
    scenario = Scenario(seed=int(seed), people=people, years=years, employer_change_pct=employer, promotion_pct=promotion, occupation_change_pct=role)
    spells, events = _dataset(scenario)
    _, baseline = _dataset(Scenario(seed=int(seed), people=people, years=years))
    with st.expander("Cohort filters", expanded=True):
        columns = st.columns(3)
        origin = columns[0].selectbox("Origin occupation", ["All"] + sorted({r["origin"] for r in events}), key="mob_origin")
        destination = columns[1].selectbox("Destination occupation", ["All"] + sorted({r["destination"] for r in events}), key="mob_dest")
        geography = columns[2].selectbox("Geography", ["All"] + sorted({r["geography"] for r in events}), key="mob_geo")
        columns = st.columns(3)
        level = columns[0].selectbox("Origin seniority", ["All"] + list(LEVELS) + ["Not employed"], key="mob_level")
        industry = columns[1].selectbox("Origin industry", ["All"] + sorted({r["origin_industry"] for r in events}), key="mob_ind")
        category = columns[2].selectbox("Exclusive transition group", ["All"] + sorted({r["category"] for r in events}), key="mob_category")
        columns = st.columns(2)
        destination_level = columns[0].selectbox("Destination seniority", ["All"] + list(LEVELS) + ["Not employed"], key="mob_destination_level")
        destination_industry = columns[1].selectbox("Destination industry", ["All"] + sorted({r["destination_industry"] for r in events}), key="mob_destination_industry")
        columns = st.columns(2)
        experience = columns[0].slider("Origin experience (years)", 0, 25, (0, 25), key="mob_exp")
        period = columns[1].slider("Transition year", 2022, 2021 + years - 1, (2022, 2021 + years - 1), key=f"mob_period_{years}")
    args = (origin, destination, level, industry, destination_level, destination_industry, geography, experience, period)
    cohort = _filter(events, *args, category)
    baseline_cohort = _filter(baseline, *args, category)
    flows = _flows(cohort)
    if not cohort:
        st.info("No synthetic events match these filters. Broaden the cohort.")
        return
    st.caption(f"{LABEL} · {VERSION} · {len(cohort):,} transition events. All visual panels below use the same selected cohort; the network and Sankey display only the top flows.")
    selection = st.selectbox("Inspect a flow (keyboard accessible)", ["All filtered flows"] + [f"{r['origin']} → {r['destination']}" for r in flows], key="mob_flow")
    if selection != "All filtered flows":
        cohort = [r for r in cohort if f"{r['origin_state']} → {r['destination_state']}" == selection]
        baseline_cohort = [r for r in baseline_cohort if f"{r['origin_state']} → {r['destination_state']}" == selection]
        flows = _flows(cohort)
    metrics = salary_metrics(cohort)
    columns = st.columns(4)
    columns[0].metric("Transition events", metrics["events"])
    columns[1].metric("Distinct people", metrics["people"])
    columns[2].metric("Valid salary pairs", metrics["valid_pairs"])
    columns[3].metric("Excluded pairs", metrics["excluded_pairs"])
    st.caption(f"Valid pairs represent {metrics['valid_people']} distinct people. Repeat events are transition-weighted. Minimum {MIN_PAIRS} valid pairs for salary comparisons; this is a stability guard, not a representativeness test.")
    max_edges = st.slider("Maximum visible flows", 5, 40, 20, key="mob_edges")
    tabs = st.tabs(["Radial network", "Flow diagram", "Transition heatmap"])
    with tabs[0]:
        st.plotly_chart(_radial(flows[:max_edges]), width="stretch")
        st.caption("Blue: positive median change; orange: negative; grey: fewer than 20 valid pairs. Colour saturates at ±20%; tooltips retain the exact median. Self loops are stayers within a career state. Use the flow selector and table for exact direction, counts and values.")
    with tabs[1]:
        st.plotly_chart(_sankey(flows[:max_edges]), width="stretch")
    with tabs[2]:
        frame = pd.DataFrame(cohort)
        matrix = pd.crosstab(frame["origin"], frame["destination"])
        chart = go.Figure(go.Heatmap(z=matrix.values, x=matrix.columns, y=matrix.index, colorscale="Blues", colorbar=dict(title="Events"),
                         hovertemplate="From %{y} → %{x}<br>Events: %{z}<br>" + LABEL + " · " + VERSION + "<extra></extra>"))
        st.plotly_chart(_figure(chart, "Occupation transitions · event counts"), width="stretch")
    if metrics["comparison_available"]:
        columns = st.columns(3)
        columns[0].metric("Median individual change", f"{metrics['median_individual_pct_change']:.1f}%")
        columns[1].metric("Individual-change IQR", f"{metrics['individual_change_iqr']:.1f} pp")
        columns[2].metric("Share with pay decrease", f"{100 * metrics['share_decreased']:.1f}%")
        st.caption(f"Median before €{metrics['median_before_salary']:,.0f}; median after €{metrics['median_after_salary']:,.0f}. Change between cohort medians: {metrics['change_between_cohort_medians_pct']:.1f}% — a different statistic from median individual change.")
        valid = [r for r in cohort if r["valid_pair"]]
        fig = go.Figure()
        for name, field in (("Before", "before_salary"), ("After", "after_salary")):
            fig.add_trace(go.Histogram(x=[r[field] for r in valid], name=name, opacity=.6,
                          hovertemplate="Annual FTE EUR %{x}<br>Events: %{y}<br>" + LABEL + " · " + VERSION + "<extra></extra>"))
        fig.update_layout(barmode="overlay", xaxis_title="Annual FTE base salary (EUR)", yaxis_title="Transition count")
        st.plotly_chart(_figure(fig, "Paired salary distributions · transition-weighted"), width="stretch")
    else:
        st.info("Salary comparisons suppressed: fewer than 20 valid pairs. Individual synthetic records remain available for inspection.")
    st.subheader("Descriptive comparisons")
    comparison = []
    # Stayers retain the experience/occupation/geography filters, but replace move category.
    stayers = _filter(events, *args, "Stayer")
    for name, rows in (("Named baseline (4 / 8 / 2)", baseline_cohort), ("Adjusted scenario", cohort), ("Stayers within cohort filters", stayers)):
        values = salary_metrics(rows)
        comparison.append({"scenario": name, "events": values["events"], "people": values["people"], "valid_pairs": values["valid_pairs"],
                           "median_individual_change_pct": values["median_individual_pct_change"] if values["comparison_available"] else None,
                           "data_label": LABEL, "generator_version": VERSION})
    st.dataframe(pd.DataFrame(comparison), hide_index=True, width="stretch")
    st.caption("Same seed and structural events across scenarios; only pay assumptions differ. Stayers replace the transition-group filter and retain other cohort filters; they can be empty for incompatible origin/destination selections. No causal inference or real-world salary prediction.")
    person = st.selectbox("Inspect a synthetic person’s complete trajectory", sorted({r["person_id"] for r in cohort}), key="mob_person")
    history = [r for r in spells if r["person_id"] == person]
    timeline = go.Figure(go.Scatter(x=[r["start_date"] for r in history], y=[r["salary_eur_annual_fte"] for r in history], mode="lines+markers", connectgaps=False,
                 text=[f"{r['occupation']} / {r['seniority']}" for r in history],
                 hovertemplate="%{x}<br>%{text}<br>Annual FTE EUR %{y:,.0f}<br>" + LABEL + " · " + VERSION + "<extra></extra>"))
    st.plotly_chart(_figure(timeline, f"Complete example history · {person} (breaks shown as gaps)"), width="stretch")
    with st.expander("Equivalent cohort table and synthetic records"):
        safe_flows = [{k: v for k, v in r.items() if r["comparison_available"] or k not in ("median_individual_pct_change", "individual_change_iqr", "median_before_salary", "median_after_salary", "change_between_cohort_medians_pct", "share_decreased")} for r in flows]
        st.dataframe(pd.DataFrame(safe_flows), hide_index=True, width="stretch")
        st.dataframe(pd.DataFrame(history), hide_index=True, width="stretch")
    filters = dict(zip(("origin", "destination", "origin_seniority", "origin_industry", "destination_seniority", "destination_industry", "geography", "experience", "period"), args))
    export = {"metadata": metadata(scenario), "filters": {**filters, "category": category, "selected_flow": selection},
              "metrics": {k: v for k, v in metrics.items() if metrics["comparison_available"] or k not in ("median_individual_pct_change", "individual_change_iqr", "median_before_salary", "median_after_salary", "change_between_cohort_medians_pct", "share_decreased")},
              "cohorts": safe_flows if flows else [], "comparisons": comparison}
    st.download_button("Download labelled synthetic cohort report (JSON)", json.dumps(export, indent=2), "synthetic-mobility-cohorts.json", "application/json")
    st.caption("Analyst next questions: do patterns persist within experience and seniority bands? Which filters leave sparse groups? How sensitive is the result to assumed move increments? Reversals and pay cuts are scenario outcomes, not evidence about real people.")

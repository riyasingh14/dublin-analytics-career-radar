"""Shared, deterministic cohort selections for the synthetic career lab."""
from __future__ import annotations
from collections import defaultdict
from career_radar.mobility import salary_metrics, MIN_PAIRS

CATEGORICAL = ('origin', 'destination', 'geography', 'category', 'origin_seniority',
               'destination_seniority', 'origin_industry', 'destination_industry')
NUMERIC = ('experience_min', 'experience_max', 'year_min', 'year_max')
SALARY_FIELDS = {'median_individual_pct_change', 'individual_change_iqr', 'median_before_salary',
                'median_after_salary', 'change_between_cohort_medians_pct', 'share_decreased'}


def validate_filters(filters):
    if not isinstance(filters, dict) or set(filters) - set(CATEGORICAL + NUMERIC):
        raise ValueError('Unknown cohort filter.')
    for name, value in filters.items():
        if not isinstance(value, str) or len(value) > 150:
            raise ValueError('Cohort filters must be text of at most 150 characters.')
        if name in NUMERIC and value:
            if not value.isdigit() or not 0 <= int(value) <= 2100:
                raise ValueError('Cohort bounds must be non-negative whole numbers.')
    for lower, upper in (('experience_min', 'experience_max'), ('year_min', 'year_max')):
        if filters.get(lower) and filters.get(upper) and int(filters[lower]) > int(filters[upper]):
            raise ValueError('Cohort minimum cannot exceed its maximum.')
    return filters


def select_cohort(rows, filters, flow='', category=None):
    """Apply the same occupation/state/band/period cuts to every linked view."""
    selected = []
    for row in rows:
        matches = all(value in ('', 'All') or row.get(name) == value
                      for name, value in filters.items() if name in CATEGORICAL and name != 'category')
        chosen_category = category if category is not None else filters.get('category', '')
        matches = matches and (chosen_category in ('', 'All') or row['category'] == chosen_category)
        for name, value in filters.items():
            if name not in NUMERIC or not value:
                continue
            observed = int(row['date'][:4]) if name.startswith('year') else row['experience_years']
            matches = matches and (observed >= int(value) if name.endswith('min') else observed <= int(value))
        if flow:
            matches = matches and row['origin_state'] + ' → ' + row['destination_state'] == flow
        if matches:
            selected.append(row)
    return selected


def guarded_metrics(rows):
    values = salary_metrics(rows)
    return {key: None if key in SALARY_FIELDS and not values['comparison_available'] else value
            for key, value in values.items()}


def flow_metrics(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['origin_state'], row['destination_state']].append(row)
    return sorted(({'origin': a, 'destination': b, **guarded_metrics(group)}
                   for (a, b), group in groups.items()),
                  key=lambda row: (-row['events'], row['origin'], row['destination']))


def cohort_details(rows):
    """Exact synthetic event evidence; capped with an explicit total and no hidden sampling."""
    return {'transition_rows': sorted(rows, key=lambda row: (row['date'], row['transition_id']))[:200],
            'transition_rows_total': len(rows), 'transition_rows_limit': 200,
            'salary_comparison_minimum': MIN_PAIRS}


def origin_stayer_reference(events, filters, selected_cohort):
    """Descriptive stayers from the selected origin states, not destination states.

    A promotion/occupation-change destination is impossible for a stayer. This
    reference deliberately releases destination, selected flow and category cuts,
    while preserving origin geography/industry/seniority/experience/period cuts.
    It is a different reference cohort, never a matched causal control group.
    """
    origin_states = {row['origin_state'] for row in selected_cohort}
    if not origin_states:
        return []
    kept = {name: value for name, value in filters.items()
            if name in {'origin', 'geography', 'origin_seniority', 'origin_industry', *NUMERIC}}
    return [row for row in select_cohort(events, kept, category='Stayer')
            if row['origin_state'] in origin_states]

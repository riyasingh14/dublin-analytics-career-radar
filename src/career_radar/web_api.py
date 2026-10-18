"""Stateless public-demo API. No private snapshots, paid calls or candidate storage."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from functools import lru_cache
import math
from pathlib import Path

from career_radar.constellation import build_constellation
from career_radar.demo import constellation_demo
from career_radar.diagnostic import analyze_description
from career_radar.mobility import Scenario, derive_transitions, generate_histories, metadata, salary_metrics
from career_radar.normalise import load_taxonomy
from career_radar.readiness import assess_readiness, export_analysis, hypothetical_readiness
from career_radar.requirements_model import extract_requirements

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ('Synthetic demonstration — Junior Data Analyst\nDublin, Ireland. Permanent, hybrid.\n'
           'You will create weekly reports and explain results to stakeholders.\n'
           'SQL is required; Python is preferred. Excel is essential.\n'
           'Three years of experience is preferred. Salary: competitive salary.')
KINDS = {'required', 'preferred', 'uncertain', 'negated'}
SALARY_FIELDS = {'median_individual_pct_change', 'individual_change_iqr', 'median_before_salary',
                 'median_after_salary', 'change_between_cohort_medians_pct', 'share_decreased'}


@lru_cache(maxsize=1)
def taxonomy():
    return load_taxonomy(ROOT / 'data/reference/skills.csv')


@lru_cache(maxsize=1)
def public_snapshot():
    # Deliberately no environment-variable path to private development data.
    return constellation_demo(taxonomy())


def _object(value, name):
    if not isinstance(value, dict):
        raise ValueError(f'{name} must be an object.')
    return value


def _text(value, name, maximum=30000, required=False):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ValueError(f'{name} must be text of at most {maximum} characters' + (' and cannot be empty.' if required else '.'))
    return value


def _number(value, name, low, high, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name} must be between {low} and {high}.')
    if integer and int(value) != value:
        raise ValueError(f'{name} must be an integer.')
    return int(value) if integer else float(value)


def _suppressed(metrics):
    return {key: (None if key in SALARY_FIELDS and not metrics['comparison_available'] else value)
            for key, value in metrics.items()}


def _mobility(payload):
    params = _object(payload.get('scenario', {}), 'scenario')
    allowed = {'seed', 'people', 'years', 'employer_change_pct', 'promotion_pct', 'occupation_change_pct'}
    if set(params) - allowed:
        raise ValueError('Unknown scenario parameter.')
    values = {}
    for name, default, low, high, integer in (
        ('seed', 42, 0, 999999, True), ('people', 500, 50, 1000, True), ('years', 5, 3, 8, True),
        ('employer_change_pct', 4, -15, 20, False), ('promotion_pct', 8, -15, 20, False),
        ('occupation_change_pct', 2, -15, 20, False),
    ):
        values[name] = _number(params.get(name, default), name, low, high, integer)
    scenario = Scenario(**values)
    spells = generate_histories(scenario)
    events = derive_transitions(spells)
    baseline = derive_transitions(generate_histories(Scenario(seed=scenario.seed, people=scenario.people, years=scenario.years)))
    filters = _object(payload.get('filters', {}), 'filters')
    fields = ('origin', 'destination', 'geography', 'category', 'origin_seniority', 'destination_seniority', 'origin_industry', 'destination_industry')
    if set(filters) - set(fields):
        raise ValueError('Unknown cohort filter.')
    for name, value in filters.items():
        _text(value, name, 150)
    def select(rows, category=None):
        return [row for row in rows if all(
            value in ('', 'All') or row.get(name) == value
            for name, value in {**filters, **({'category': category} if category is not None else {})}.items())]
    cohort, base_cohort = select(events), select(baseline)
    selection = _text(payload.get('flow', ''), 'flow', 300)
    if selection:
        cohort = [row for row in cohort if row['origin_state'] + ' → ' + row['destination_state'] == selection]
        base_cohort = [row for row in base_cohort if row['origin_state'] + ' → ' + row['destination_state'] == selection]
    grouped = defaultdict(list)
    for row in cohort:
        grouped[(row['origin_state'], row['destination_state'])].append(row)
    flows = [{'origin': origin, 'destination': destination, **_suppressed(salary_metrics(rows))}
             for (origin, destination), rows in grouped.items()]
    flows.sort(key=lambda row: (-row['events'], row['origin'], row['destination']))
    metrics = _suppressed(salary_metrics(cohort))
    comparisons = [{'name': name, **_suppressed(salary_metrics(rows))}
                   for name, rows in [('Named baseline (4 / 8 / 2)', base_cohort),
                                      ('Adjusted scenario', cohort), ('Stayers within cohort filters', select(events, 'Stayer'))]]
    people_ids = sorted({row['person_id'] for row in cohort})
    person = _text(payload.get('person_id', ''), 'person_id', 30)
    if person not in people_ids:
        person = people_ids[0] if people_ids else ''
    trajectory = [row for row in spells if row['person_id'] == person]
    valid = [row for row in cohort if row['valid_pair']] if metrics['comparison_available'] else []
    return {'metadata': metadata(scenario), 'metrics': metrics, 'flows': flows,
            'comparisons': comparisons, 'trajectory': trajectory, 'people_ids': people_ids,
            'selected_person': person, 'distributions': {'before': [r['before_salary'] for r in valid], 'after': [r['after_salary'] for r in valid]},
            'filters': filters, 'flow': selection,
            'occupation_options': sorted({r['origin'] for r in events} | {r['destination'] for r in events}),
            'category_options': sorted({r['category'] for r in events}),
            'geography_options': sorted({r['geography'] for r in events}),
            'industry_options': sorted({r['origin_industry'] for r in events} | {r['destination_industry'] for r in events})}


def dispatch(action, payload=None):
    payload = _object({} if payload is None else payload, 'Request')
    if action == 'health':
        return {'status': 'ok', 'version': 'web-v1', 'data_mode': 'synthetic-demo'}
    if action == 'bootstrap':
        return {'snapshot': public_snapshot(), 'taxonomy': [asdict(skill) for skill in taxonomy()],
                'example_description': EXAMPLE, 'data_mode': 'synthetic-demo'}
    if action == 'constellation':
        role, geography = payload.get('role') or None, payload.get('geography') or None
        if role is not None: _text(role, 'role', 100)
        if geography is not None: _text(geography, 'geography', 100)
        count = _number(payload.get('min_pair_count', 5), 'min_pair_count', 1, 100, True)
        sample = _number(payload.get('min_sample_size', 20), 'min_sample_size', 1, 1000, True)
        return build_constellation(public_snapshot(), role=role, geography=geography,
                                   min_pair_count=count, min_sample_size=sample)
    if action in ('diagnostic', 'readiness'):
        text = _text(payload.get('text'), 'Description', required=True)
        if action == 'diagnostic':
            return analyze_description(text, taxonomy())
        requirements = extract_requirements(text, taxonomy())
        overrides = _object(payload.get('classifications', {}), 'classifications')
        evidence = _object(payload.get('evidence', {}), 'evidence')
        identifiers = {r['requirement_id'] for r in requirements}
        if (set(overrides) | set(evidence)) - identifiers:
            raise ValueError('Requirements changed. Re-extract them before assessment.')
        for kind in overrides.values():
            if kind not in KINDS: raise ValueError('Unknown requirement classification.')
        for item in evidence.values():
            _object(item, 'evidence item')
            if item.get('status', 'unknown') not in {'unknown', 'supported', 'partial', 'missing'}:
                raise ValueError('Unknown evidence status.')
            _text(item.get('note', ''), 'Evidence note', 500)
        reviewed = [{**r, 'requirement_type': overrides.get(r['requirement_id'], r['requirement_type']),
                     'extracted_requirement_type': r['requirement_type'],
                     'classification_provenance': 'user-confirmed' if r['requirement_id'] in overrides else 'rule-extracted',
                     'classification_corrected': overrides.get(r['requirement_id'], r['requirement_type']) != r['requirement_type']}
                    for r in requirements]
        result = assess_readiness(reviewed, evidence)
        output = {'requirements': requirements, 'assessment': result, 'report': export_analysis(result), 'scenario': None}
        if payload.get('hypothetical') is not None:
            hypothetical = _object(payload['hypothetical'], 'hypothetical')
            identifier = _text(hypothetical.get('requirement_id'), 'Hypothetical requirement', 100, required=True)
            note = _text(hypothetical.get('note'), 'Planned evidence', 500, required=True)
            output['scenario'] = hypothetical_readiness(reviewed, evidence, identifier, note)
        return output
    if action == 'mobility':
        return _mobility(payload)
    raise ValueError('Unknown analytical action.')

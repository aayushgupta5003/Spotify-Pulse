# Spotify Pulse — Implementation Plan

## 1. Objective

Complete Spotify Pulse as a coherent, reproducible Spotify-inspired
Product Analytics and Data Science platform.

The final project should demonstrate:

- data engineering
- data cleaning
- data modeling
- SQL analytics
- exploratory data analysis
- product analytics
- churn prediction
- user segmentation
- experimentation
- recommendation analytics
- Streamlit dashboarding
- business insight generation

The implementation should remain appropriate for a 4–6 week student
portfolio project.

---

# 2. Execution Principles

Codex should implement the project incrementally.

For each phase:

1. Inspect existing implementation.
2. Implement the required changes.
3. Validate the result.
4. Run relevant tests/checks.
5. Inspect generated outputs.
6. Update documentation if necessary.
7. Only then move to the next phase.

Do not blindly rewrite existing notebooks or source code.

Reuse working components where appropriate.

Move reusable logic from notebooks into `src/` when the implementation
becomes stable.

Notebooks should primarily be used for exploration, analysis, and
validation.

---

# 3. Phase 0 — Repository Audit

## Objective

Understand the current state of the repository before making substantial
changes.

## Tasks

Inspect:

- repository structure
- `AGENTS.md`
- `docs/PROJECT_CONTEXT.md`
- this implementation plan
- existing PRD
- `README.md`
- `requirements.txt`
- existing notebooks
- existing source code
- existing processed datasets
- raw dataset schemas

Verify:

- current Python environment
- installed dependencies
- Git status
- existing data files
- existing notebook outputs
- whether processed files match their intended schemas

## Important

Do not modify raw data.

Do not delete existing analysis simply because it is incomplete.

## Deliverable

A short repository audit documenting:

- what is already complete
- what is partially complete
- what is missing
- any inconsistencies
- recommended implementation order

---

# 4. Phase 1 — Data Pipeline Foundation

## Objective

Create a reliable and reproducible data-processing pipeline.

## Inputs

Raw datasets:

- `spotify_streaming_history.csv`
- `spotify_user_behavior.csv`
- `spotify_user_preferences.xlsx`

## Tasks

Create reusable data-processing code under `src/`.

The proposed module list below is illustrative. Phase 1 has no justified
cross-dataset integration responsibility, so `integration.py` is intentionally
omitted. The implemented loader, cleaning, validation, and pipeline modules
are described in `docs/DATA_PIPELINE.md`.

Phase 1 creates only these processed tables: `users`, `user_behavior`,
`tracks`, and `streaming_events`. Do not add `user_id` to streaming events
or assign preference profiles to behavior users. Streaming history and
preferences have no user identifier; any such relationship would be synthetic
and is outside this phase. The preference workbook remains raw and is not
read by the Phase 1 pipeline.

Preserve the current notebook's cleaning rules: remove exact duplicate
streaming rows, fill missing `reason_start` and `reason_end` with `unknown`,
and preserve preference missingness (no preference table is produced in this
phase). Generate surrogate IDs in stable first-seen source order so unchanged
inputs produce identical IDs.

Validate raw and processed schemas, row counts, nulls, duplicates,
primary-key uniqueness, data types, and the `streaming_events.track_id` to
`tracks.track_id` and `user_behavior.user_id` to `users.user_id` relationships.
Write outputs only beneath `data/processed/`; never modify `data/raw/`.

Run from the repository root with `python -m src.data.pipeline`. Phase 1 is
complete when the four tables can be reproduced and all validation checks
pass. Later project phases are not part of this step.

Potential modules:

```text
src/
├── data/
│   ├── __init__.py
│   ├── load.py
│   ├── cleaning.py
│   ├── validation.py
│   └── integration.py
```

## 5. Phase 2 — Analytical Model and Synthetic Preference Integration

Phase 2 retains the four Phase 1 tables and adds only
`data/processed/user_preferences.csv` plus a mapping metadata JSON. The
preference table has one row per behavior user, but each survey assignment is
synthetic. Never add `user_id` to `streaming_events`.

Treat all 520 survey responses as the preference source distribution. Expand
each response proportionally to 15 or 16 assignments, then solve a global
capacity-constrained assignment maximizing age-band and normalized-gender
compatibility. These are soft signals, not hard constraints; use a fixed seed
only for tied quotas and assignments. Do not use other behavior signals
without a demonstrated semantic correspondence in source fields. Retain
per-row source-response and compatibility diagnostics, and report
category-distribution drift against the survey.

Run `python -m src.data.integration` to regenerate Phase 1 and Phase 2 outputs
together. Validate profile quotas, user coverage and uniqueness, demographic
compatibility diagnostics, category margins, structural missingness, and
reproducibility. Do not begin SQL analytics, EDA, ML, experimentation, or
dashboard work until Phase 2 is reviewed and complete.
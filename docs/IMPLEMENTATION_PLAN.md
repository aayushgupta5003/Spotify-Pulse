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

Potential modules:

```text
src/
├── data/
│   ├── __init__.py
│   ├── load.py
│   ├── cleaning.py
│   ├── validation.py
│   └── integration.py
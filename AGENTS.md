# Spotify Pulse - Codex Instructions

## Project

Spotify Pulse is a portfolio-grade Spotify-inspired Product Analytics
and Data Science platform.

The project combines:

- Data Engineering
- SQL Analytics
- Product Analytics
- Machine Learning
- Experimentation
- Streamlit Dashboarding

## Primary Goal

Build a coherent, reproducible analytics system rather than a collection
of disconnected notebooks.

The final project should demonstrate practical skills relevant to
Data Analyst, Product Analyst, and Data Science internship roles.

## Source of Truth

Before making substantial changes, read:

- `docs/PROJECT_CONTEXT.md`
- `docs/IMPLEMENTATION_PLAN.md`
- the existing project PRD
- relevant existing source code and notebooks

Treat these documents as the source of truth for project requirements
and architectural decisions.

If there is a contradiction between existing code and the documented
requirements, inspect the situation and explain the conflict before
making a major change.

## Working Principles

1. Inspect the existing repository before modifying anything.
2. Do not overwrite existing work without understanding it.
3. Preserve the raw datasets.
4. Keep synthetic data generation deterministic with explicit random seeds.
5. Clearly document every synthetic-data assumption.
6. Never represent synthetic relationships as real Spotify relationships.
7. Prefer reusable Python modules over duplicated notebook code.
8. Keep notebooks primarily for exploration, analysis, and validation.
9. Put reusable production logic under `src/`.
10. Validate every major transformation.
11. Add appropriate tests and data-quality checks.
12. Do not silently invent business logic when requirements are ambiguous.
13. When an architectural decision is unclear, document the decision and
    explain the tradeoff before implementing it.
14. Keep the implementation understandable for a student portfolio project.
15. Avoid unnecessary over-engineering.

## Data Integrity

The three source datasets are not naturally relational.

- User Behavior contains `user_id`.
- Streaming History does not contain `user_id`.
- User Preferences does not contain `user_id`.

Therefore, relationships created between these datasets are synthetic
and must be explicitly documented.

Do not create arbitrary random mappings simply to make joins work.

Synthetic mappings should use meaningful constraints from the available
data, including demographics, behavior, and preferences where appropriate.

## Raw Data

Never modify files inside:

`data/raw/`

All transformations must create processed or derived datasets elsewhere.

## Reproducibility

Synthetic data generation, sampling, simulations, and machine-learning
experiments must use explicit random seeds where applicable.

The same inputs and configuration should produce reproducible results
unless nondeterminism is intentionally required and documented.

## Scope

The project should remain feasible as a 4-6 week portfolio project.

Avoid unnecessary:

- microservices
- complex distributed systems
- excessive database infrastructure
- unnecessarily complicated recommender systems
- excessive numbers of ML models
- features that do not contribute to the project's core objective

Prioritize depth and coherence over feature count.

## Git

Do not rewrite Git history.

Do not amend existing commits unless explicitly asked.

Create focused commits for meaningful changes.

Do not commit secrets, credentials, API keys, or environment-specific
private configuration.

## Validation

A feature is not complete merely because the code runs.

Before considering a major feature complete:

- validate the transformation
- check relevant row counts
- check schema and data types
- check missing values where appropriate
- check duplicate behavior where relevant
- run relevant tests
- inspect important outputs
- update documentation when assumptions or architecture change

## Documentation

Keep documentation synchronized with the implementation.

If a major architectural or data-generation decision changes,
update the relevant documentation.

## Definition of Done

A feature is complete only when it is:

- reproducible
- documented
- validated
- integrated with the existing architecture
- consistent with the project requirements
- understandable to another developer reviewing the repository
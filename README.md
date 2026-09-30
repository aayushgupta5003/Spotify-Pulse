# Spotify Pulse

A Spotify-inspired product analytics and data science portfolio project. The
current implementation includes a reproducible Phase 1 data pipeline and a
controlled, explicitly synthetic Phase 2 integration of survey preferences.

## Run the data pipeline

From the repository root, run `python -m src.data.pipeline`. The pipeline
validates its inputs and outputs before completing. See
[docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) for the transformations,
validation rules, and data-linkage limitations.

## Build the analytical model

Run `python -m src.data.integration` from the repository root to regenerate
the four Phase 1 tables and create `user_preferences.csv`. The assigned
preference profiles are synthetic and are not real Spotify user relationships.

# Spotify Pulse

A Spotify-inspired product analytics and data science portfolio project. The
current implementation includes a reproducible Phase 1 data pipeline that
builds user, behavior, track, and streaming event tables from the raw sources.

## Run the data pipeline

From the repository root, run `python -m src.data.pipeline`. The pipeline
validates its inputs and outputs before completing. See
[docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) for the transformations,
validation rules, and data-linkage limitations.

# Phase 1 Data Pipeline

Run from the repository root:

```powershell
python -m src.data.pipeline
```

The pipeline reads `data/raw/spotify_streaming_history.csv` and
`data/raw/spotify_user_behavior.csv`. It writes exactly four CSVs under
`data/processed/`: `users.csv`, `user_behavior.csv`, `tracks.csv`, and
`streaming_events.csv`. It does not read or modify the preference workbook.

## Transformations

- Remove exact duplicate rows from streaming history.
- Fill missing streaming `reason_start` and `reason_end` values with
  `unknown`.
- Build the track dimension from first-seen unique combinations of track URI,
  track name, artist name, and album name.
- Assign sequential `track_id` and `stream_id` values in first-seen source
  order. The same unchanged, ordered input reproduces the same IDs.
- Split behavior records into `users` (user ID, age, gender, country) and
  `user_behavior` (remaining user metrics), as in the existing notebook.

No user identifier is added to streaming events, and preference profiles are
not assigned to behavior users. These datasets have no shared user key; any
future linkage would be synthetic and requires a separately documented
method.

## Validation

Before writing, the pipeline checks source and output schemas, expected row
counts derived from raw inputs and documented deduplication, nulls, duplicate
rows, primary-key uniqueness, data types, and the two valid relationships:
`user_behavior.user_id` to `users.user_id`, and
`streaming_events.track_id` to `tracks.track_id`. It reloads and validates
the written CSVs as well. Validation failures stop the run with a list of
issues.

The current source data produces 8,000 users, 8,000 behavior rows, 16,597
tracks, and 148,675 streaming events after exact duplicate removal.

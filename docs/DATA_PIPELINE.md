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

## Phase 2 Synthetic Preference Integration

Run the complete current data workflow with:

```powershell
python -m src.data.integration
```

This command first reruns and validates Phase 1, then reads the 520-response
preference workbook and writes `user_preferences.csv` plus the auditable
`user_preferences_mapping_metadata.json`. The output has one row per behavior
user, but each assigned preference profile is synthetic. Streaming history
remains separate; no `user_id` is added to streaming events.

The mapper gives each of the 520 source responses a proportional quota of 15
or 16 assignments, using largest-remainder expansion and a fixed seed for
ties. This preserves source category margins instead of sampling freely or
forcing a uniform output. A global capacitated assignment maximizes the sum
of two binary compatibility signals: the user's exact age falls within the
survey response's stated age band (inclusive endpoints), and normalized
gender matches (`Others` becomes `Other`). It has no hard demographic
constraints, allowing mismatches where necessary to retain survey quotas.
The tie-break seed is 42 by default. Listening time, songs per day, skip
rate, offline listening, subscription distinctions, and device categories
are not used as matching signals because the survey fields do not provide
defensible equivalents.

Every output row records its source spreadsheet row, age/gender match flags,
the 0–2 compatibility score, and a human-readable rationale. The JSON
metadata records the seed, input hashes, assignment method, match summary,
source/output category counts, maximum category share difference, and total
variation distance for every preference column. Validation requires unique
coverage of all users, exact source-response quotas, correct match
diagnostics, preserved structural missingness, and per-field category drift
below 0.5 percentage points (total variation below 1%).

With the current inputs and seed 42, 3,928 assignments (49.1%) match the
survey age band, 4,644 (58.1%) match normalized gender, and 2,343 (29.3%)
match both. The global assignment scores 1,771 (22.1%) as matching neither
signal. Across the 18 preference attributes, the largest observed category
share difference is 0.138 percentage points (`preffered_premium_plan`); the
largest total variation distance is 0.00305 (`music_lis_frequency`). For
example, Music/Podcast maps to 6,305/1,695 users versus 410/110 source
responses, and recommendation ratings map to 213/862/2,922/2,678/1,325 for
ratings 1–5 versus source counts 14/56/190/174/86. Detailed source and mapped
counts for every category are stored in the metadata JSON.

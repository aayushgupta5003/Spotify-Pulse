"""Schema, quality, key, row-count, and relationship checks."""

from collections.abc import Mapping

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_float_dtype,
    is_integer_dtype,
    is_string_dtype,
)

from .cleaning import BEHAVIOR_COLUMNS, EVENT_COLUMNS, TRACK_COLUMNS, USER_COLUMNS


class DataValidationError(ValueError):
    """Raised when one or more Phase 1 validation checks fail."""


EXPECTED_COLUMNS = {
    "users": USER_COLUMNS,
    "user_behavior": BEHAVIOR_COLUMNS,
    "tracks": ["track_id", *TRACK_COLUMNS],
    "streaming_events": EVENT_COLUMNS,
}
PRIMARY_KEYS = {"users": "user_id", "user_behavior": "user_id", "tracks": "track_id", "streaming_events": "stream_id"}
INTEGER_COLUMNS = {
    "users": ["user_id", "age"],
    "user_behavior": ["user_id", "listening_time", "songs_played_per_day", "ads_listened_per_week", "offline_listening", "is_churned"],
    "tracks": ["track_id"],
    "streaming_events": ["stream_id", "ms_played", "track_id"],
}
BOOLEAN_COLUMNS = {"streaming_events": ["shuffle", "skipped"]}
FLOAT_COLUMNS = {"user_behavior": ["skip_rate"]}
STRING_COLUMNS = {
    "users": ["gender", "country"],
    "user_behavior": ["subscription_type", "device_type"],
    "tracks": TRACK_COLUMNS,
    "streaming_events": ["ts", "platform", "reason_start", "reason_end"],
}
RAW_STREAMING_COLUMNS = [
    "spotify_track_uri", "ts", "platform", "ms_played", "track_name",
    "artist_name", "album_name", "reason_start", "reason_end", "shuffle", "skipped",
]
RAW_BEHAVIOR_COLUMNS = [
    "user_id", "gender", "age", "country", "subscription_type", "listening_time",
    "songs_played_per_day", "skip_rate", "device_type", "ads_listened_per_week",
    "offline_listening", "is_churned",
]


def validate_raw_schemas(streaming: pd.DataFrame, behavior: pd.DataFrame) -> list[str]:
    """Check the raw inputs required by the Phase 1 transformation."""
    failures = []
    for name, frame, columns in (
        ("streaming history", streaming, RAW_STREAMING_COLUMNS),
        ("user behavior", behavior, RAW_BEHAVIOR_COLUMNS),
    ):
        if list(frame.columns) != columns:
            failures.append(f"{name}: expected columns {columns}, got {list(frame.columns)}")
    if failures:
        raise DataValidationError("Raw schema validation failed:\n- " + "\n- ".join(failures))
    return ["raw streaming history: schema matches", "raw user behavior: schema matches"]


def validate_processed_tables(
    tables: Mapping[str, pd.DataFrame], expected_rows: Mapping[str, int] | None = None
) -> list[str]:
    """Validate four tables and return human-readable passing check results.

    Raises ``DataValidationError`` with all detected failures rather than
    stopping at the first issue.
    """
    failures: list[str] = []
    checks: list[str] = []
    required_tables = set(EXPECTED_COLUMNS)
    if set(tables) != required_tables:
        failures.append(
            f"Expected exactly {sorted(required_tables)}; received {sorted(tables)}"
        )
    for name, expected_columns in EXPECTED_COLUMNS.items():
        if name not in tables:
            continue
        frame = tables[name]
        if list(frame.columns) != expected_columns:
            failures.append(f"{name}: schema mismatch; expected {expected_columns}, got {list(frame.columns)}")
        else:
            checks.append(f"{name}: schema and column order match")
        if expected_rows is not None and name in expected_rows:
            if len(frame) != expected_rows[name]:
                failures.append(f"{name}: expected {expected_rows[name]} rows, got {len(frame)}")
            else:
                checks.append(f"{name}: row count is {len(frame)}")
        nulls = int(frame.isna().sum().sum())
        if nulls:
            failures.append(f"{name}: contains {nulls} null values")
        else:
            checks.append(f"{name}: no null values")
        duplicates = int(frame.duplicated().sum())
        if duplicates:
            failures.append(f"{name}: contains {duplicates} duplicate rows")
        else:
            checks.append(f"{name}: no duplicate rows")
        key = PRIMARY_KEYS[name]
        if key not in frame.columns:
            failures.append(f"{name}: missing primary-key column {key}")
            continue
        if frame[key].isna().any() or frame[key].duplicated().any():
            failures.append(f"{name}.{key}: primary key is null or non-unique")
        else:
            checks.append(f"{name}.{key}: primary key is unique and non-null")
        for column in INTEGER_COLUMNS.get(name, []):
            if column in frame.columns and not is_integer_dtype(frame[column].dtype):
                failures.append(f"{name}.{column}: expected integer dtype, got {frame[column].dtype}")
        for column in BOOLEAN_COLUMNS.get(name, []):
            if column in frame.columns and not is_bool_dtype(frame[column].dtype):
                failures.append(f"{name}.{column}: expected boolean dtype, got {frame[column].dtype}")
        for column in FLOAT_COLUMNS.get(name, []):
            if column in frame.columns and not is_float_dtype(frame[column].dtype):
                failures.append(f"{name}.{column}: expected floating-point dtype, got {frame[column].dtype}")
        for column in STRING_COLUMNS.get(name, []):
            if column in frame.columns and not is_string_dtype(frame[column].dtype):
                failures.append(f"{name}.{column}: expected string dtype, got {frame[column].dtype}")
    if "user_id" not in tables.get("users", pd.DataFrame()).columns:
        failures.append("users.user_id is required for the user_behavior relationship")
    elif "user_id" in tables.get("user_behavior", pd.DataFrame()).columns:
        users = set(tables["users"]["user_id"])
        behavior_users = set(tables["user_behavior"]["user_id"])
        if behavior_users - users:
            failures.append("user_behavior.user_id contains values absent from users.user_id")
        else:
            checks.append("user_behavior.user_id references users.user_id")
    if "track_id" in tables.get("tracks", pd.DataFrame()).columns and "track_id" in tables.get("streaming_events", pd.DataFrame()).columns:
        track_ids = set(tables["tracks"]["track_id"])
        event_track_ids = set(tables["streaming_events"]["track_id"])
        if event_track_ids - track_ids:
            failures.append("streaming_events.track_id contains values absent from tracks.track_id")
        else:
            checks.append("streaming_events.track_id references tracks.track_id")
    if "user_id" in tables.get("streaming_events", pd.DataFrame()).columns:
        failures.append("streaming_events must not contain user_id")
    if failures:
        raise DataValidationError("Data validation failed:\n- " + "\n- ".join(failures))
    return checks

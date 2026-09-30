"""Cleaning and table construction that reproduces the existing notebook."""

import pandas as pd


TRACK_COLUMNS = ["spotify_track_uri", "track_name", "artist_name", "album_name"]
USER_COLUMNS = ["user_id", "age", "gender", "country"]
BEHAVIOR_COLUMNS = [
    "user_id",
    "subscription_type",
    "listening_time",
    "songs_played_per_day",
    "skip_rate",
    "device_type",
    "ads_listened_per_week",
    "offline_listening",
    "is_churned",
]
EVENT_COLUMNS = [
    "stream_id",
    "ts",
    "platform",
    "ms_played",
    "reason_start",
    "reason_end",
    "shuffle",
    "skipped",
    "track_id",
]


def build_processed_tables(
    streaming: pd.DataFrame, behavior: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Build exactly the four Phase 1 processed tables.

    Exact duplicate rows are removed from streaming history, and missing
    playback reasons are filled with ``unknown`` as in the cleaning notebook.
    User preferences are intentionally not accepted by this function.

    Sequential surrogate IDs follow first-seen source order, matching the
    notebook's ``drop_duplicates().reset_index()`` behavior. For unchanged,
    ordered inputs this produces identical IDs on every run.
    """
    streaming = streaming.drop_duplicates().copy()
    streaming["reason_start"] = streaming["reason_start"].fillna("unknown")
    streaming["reason_end"] = streaming["reason_end"].fillna("unknown")

    tracks = streaming[TRACK_COLUMNS].drop_duplicates().reset_index(drop=True)
    tracks.insert(0, "track_id", range(1, len(tracks) + 1))

    events = streaming.merge(
        tracks,
        on=TRACK_COLUMNS,
        how="left",
        validate="many_to_one",
        sort=False,
    )
    events = events.drop(columns=TRACK_COLUMNS)
    events.insert(0, "stream_id", range(1, len(events) + 1))
    events = events[EVENT_COLUMNS]

    users = behavior[USER_COLUMNS].copy()
    user_behavior = behavior[BEHAVIOR_COLUMNS].copy()

    return {
        "users": users,
        "user_behavior": user_behavior,
        "tracks": tracks,
        "streaming_events": events,
    }

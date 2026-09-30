"""Run the Phase 1 data pipeline from raw files to four processed CSVs."""

from pathlib import Path

from .cleaning import TRACK_COLUMNS, build_processed_tables
from .load import PROJECT_ROOT, load_raw_datasets
from .validation import validate_processed_tables, validate_raw_schemas


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def run_pipeline(
    raw_dir: Path | None = None, processed_dir: Path | None = None
) -> dict[str, int]:
    """Build, validate, and write the four approved processed tables."""
    raw_dir = Path(raw_dir) if raw_dir is not None else PROJECT_ROOT / "data" / "raw"
    processed_dir = Path(processed_dir) if processed_dir is not None else PROCESSED_DIR
    streaming, behavior = load_raw_datasets(raw_dir)
    checks = validate_raw_schemas(streaming, behavior)
    tables = build_processed_tables(streaming, behavior)
    cleaned_streaming = streaming.drop_duplicates()
    expected_rows = {
        "users": len(behavior),
        "user_behavior": len(behavior),
        "tracks": len(cleaned_streaming[TRACK_COLUMNS].drop_duplicates()),
        "streaming_events": len(cleaned_streaming),
    }
    checks.extend(validate_processed_tables(tables, expected_rows))
    processed_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(processed_dir / f"{name}.csv", index=False)
    # Validate the serialized artifacts too, catching output/schema drift.
    import pandas as pd

    reloaded = {
        name: pd.read_csv(processed_dir / f"{name}.csv") for name in tables
    }
    validate_processed_tables(reloaded, expected_rows)
    print("Phase 1 validation passed:")
    for check in checks:
        print(f"- {check}")
    return {name: len(frame) for name, frame in tables.items()}


if __name__ == "__main__":
    counts = run_pipeline()
    print("Processed row counts:")
    for table, count in counts.items():
        print(f"- {table}: {count:,}")

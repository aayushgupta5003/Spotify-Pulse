"""Load the project's raw source datasets."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_raw_datasets(raw_dir: Path = RAW_DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load only the sources used to build the four Phase 1 output tables.

    The preference workbook is deliberately not read or transformed in Phase 1.
    It has no user identifier and is not linked to the behavior records.
    """
    raw_dir = Path(raw_dir)
    streaming = pd.read_csv(raw_dir / "spotify_streaming_history.csv")
    behavior = pd.read_csv(raw_dir / "spotify_user_behavior.csv")
    return streaming, behavior

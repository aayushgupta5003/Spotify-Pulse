"""Controlled, reproducible synthetic integration of survey preferences.

The source survey has no user key. This module expands its observed response
distribution and assigns response profiles to behavior users with a global,
capacity-constrained demographic compatibility objective. The resulting
relationships are synthetic and must not be represented as observed Spotify
user data.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .load import PROJECT_ROOT
from .pipeline import run_pipeline


DEFAULT_MAPPING_SEED = 42
MAX_CATEGORY_DELTA_PP = 0.5
MAX_TOTAL_VARIATION = 0.01
DEMOGRAPHIC_COLUMNS = ["Age", "Gender"]
PREFERENCE_COLUMNS = [
    "spotify_usage_period",
    "spotify_listening_device",
    "spotify_subscription_plan",
    "premium_sub_willingness",
    "preffered_premium_plan",
    "preferred_listening_content",
    "fav_music_genre",
    "music_time_slot",
    "music_Influencial_mood",
    "music_lis_frequency",
    "music_expl_method",
    "music_recc_rating",
    "pod_lis_frequency",
    "fav_pod_genre",
    "preffered_pod_format",
    "pod_host_preference",
    "preffered_pod_duration",
    "pod_variety_satisfaction",
]
MAPPING_COLUMNS = [
    "source_response_row",
    "mapping_age_compatible",
    "mapping_gender_compatible",
    "mapping_compatibility_score",
    "mapping_rationale",
]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class SyntheticMappingError(ValueError):
    """Raised when source profiles cannot be safely mapped or validated."""


@dataclass
class _Edge:
    to: int
    reverse_index: int
    capacity: int
    cost: int
    initial_capacity: int


def _add_edge(graph: list[list[_Edge]], source: int, target: int, capacity: int, cost: int) -> _Edge:
    forward = _Edge(target, len(graph[target]), capacity, cost, capacity)
    reverse = _Edge(source, len(graph[source]), 0, -cost, 0)
    graph[source].append(forward)
    graph[target].append(reverse)
    return forward


def _normalize_gender(value: Any) -> str:
    normalized = str(value).strip().casefold()
    mapping = {"female": "Female", "male": "Male", "other": "Other", "others": "Other"}
    if normalized not in mapping:
        raise SyntheticMappingError(f"Unsupported gender category {value!r}")
    return mapping[normalized]


def _parse_age_band(value: Any) -> tuple[int, int | None]:
    """Parse survey age labels as inclusive bounds as written in the source."""
    label = str(value).strip()
    interval = re.fullmatch(r"(\d+)\s*-\s*(\d+)", label)
    if interval:
        low, high = (int(interval.group(1)), int(interval.group(2)))
        if low > high:
            raise SyntheticMappingError(f"Invalid survey age band {value!r}")
        return low, high
    open_interval = re.fullmatch(r"(\d+)\s*\+", label)
    if open_interval:
        return int(open_interval.group(1)), None
    raise SyntheticMappingError(f"Unsupported survey age band {value!r}")


def _age_compatible(age: int, band: tuple[int, int | None]) -> bool:
    low, high = band
    return age >= low and (high is None or age <= high)


def _profile_quotas(response_count: int, user_count: int, rng: np.random.Generator) -> np.ndarray:
    """Proportionally expand each equally weighted observed response.

    Largest-remainder rounding keeps response-level weight equal, assigns
    floor/ceil of the ideal expansion count, and uses the seeded RNG only when
    the remainders tie (as they do for individual response rows).
    """
    if response_count < 1 or user_count < 1:
        raise SyntheticMappingError("Survey and user tables must both be non-empty")
    base, remainder = divmod(user_count, response_count)
    quotas = np.full(response_count, base, dtype=np.int64)
    if remainder:
        quotas[rng.permutation(response_count)[:remainder]] += 1
    return quotas


def _min_cost_transport(
    user_group_sizes: dict[tuple[int, str], int],
    survey_group_sizes: dict[tuple[str, str], int],
    compatibility: dict[tuple[tuple[int, str], tuple[str, str]], tuple[bool, bool]],
    rng: np.random.Generator,
) -> dict[tuple[tuple[int, str], tuple[str, str]], int]:
    """Globally optimize demographic compatibility subject to exact margins.

    Compatibility is the sum of two transparent binary signals: age falls in
    the survey's stated age band (inclusive), and normalized gender matches.
    Costs first maximize total compatibility; seeded tie costs can only decide
    between solutions with equal total compatibility.
    """
    user_groups = list(user_group_sizes)
    survey_groups = list(survey_group_sizes)
    total_users = sum(user_group_sizes.values())
    if total_users != sum(survey_group_sizes.values()):
        raise SyntheticMappingError("User-group supply and survey-profile demand differ")

    source = 0
    user_offset = 1
    survey_offset = user_offset + len(user_groups)
    sink = survey_offset + len(survey_groups)
    graph: list[list[_Edge]] = [[] for _ in range(sink + 1)]
    for i, group in enumerate(user_groups):
        _add_edge(graph, source, user_offset + i, user_group_sizes[group], 0)
    for j, group in enumerate(survey_groups):
        _add_edge(graph, survey_offset + j, sink, survey_group_sizes[group], 0)

    tie_bound = 1_000
    compatibility_scale = total_users * tie_bound + 1
    pair_edges: dict[tuple[tuple[int, str], tuple[str, str]], _Edge] = {}
    for i, user_group in enumerate(user_groups):
        for j, survey_group in enumerate(survey_groups):
            age_match, gender_match = compatibility[(user_group, survey_group)]
            score = int(age_match) + int(gender_match)
            tie_cost = int(rng.integers(0, tie_bound))
            pair_edges[(user_group, survey_group)] = _add_edge(
                graph,
                user_offset + i,
                survey_offset + j,
                min(user_group_sizes[user_group], survey_group_sizes[survey_group]),
                (2 - score) * compatibility_scale + tie_cost,
            )

    # Successive shortest augmenting paths with reduced-cost potentials.
    potentials = [0] * len(graph)
    flow = 0
    while flow < total_users:
        distances: list[int | None] = [None] * len(graph)
        previous: list[tuple[int, int] | None] = [None] * len(graph)
        distances[source] = 0
        queue: list[tuple[int, int]] = [(0, source)]
        while queue:
            distance, node = heapq.heappop(queue)
            if distances[node] != distance:
                continue
            for edge_index, edge in enumerate(graph[node]):
                if edge.capacity <= 0:
                    continue
                candidate = distance + edge.cost + potentials[node] - potentials[edge.to]
                if distances[edge.to] is None or candidate < distances[edge.to]:
                    distances[edge.to] = candidate
                    previous[edge.to] = (node, edge_index)
                    heapq.heappush(queue, (candidate, edge.to))
        if distances[sink] is None:
            raise SyntheticMappingError("Unable to assign every user while preserving source-profile quotas")
        for node, distance in enumerate(distances):
            if distance is not None:
                potentials[node] += distance
        amount = total_users - flow
        node = sink
        while node != source:
            step = previous[node]
            if step is None:
                raise SyntheticMappingError("Incomplete augmenting path in demographic assignment")
            parent, edge_index = step
            amount = min(amount, graph[parent][edge_index].capacity)
            node = parent
        node = sink
        while node != source:
            parent, edge_index = previous[node]  # type: ignore[misc]
            edge = graph[parent][edge_index]
            edge.capacity -= amount
            graph[node][edge.reverse_index].capacity += amount
            node = parent
        flow += amount

    return {
        pair: edge.initial_capacity - edge.capacity
        for pair, edge in pair_edges.items()
        if edge.initial_capacity != edge.capacity
    }


def _category_key(value: Any) -> tuple[str, str]:
    if pd.isna(value):
        return ("missing", "")
    return (type(value).__name__, str(value))


def _distribution_report(source: pd.Series, assigned: pd.Series, sample_size: int) -> dict[str, Any]:
    source_counts = Counter(_category_key(value) for value in source.tolist())
    assigned_counts = Counter(_category_key(value) for value in assigned.tolist())
    category_keys = sorted(set(source_counts) | set(assigned_counts))
    rows = []
    source_n = len(source)
    max_delta_pp = 0.0
    total_variation = 0.0
    for key in category_keys:
        source_count = source_counts[key]
        assigned_count = assigned_counts[key]
        source_share = source_count / source_n
        assigned_share = assigned_count / sample_size
        delta_pp = (assigned_share - source_share) * 100
        max_delta_pp = max(max_delta_pp, abs(delta_pp))
        total_variation += abs(assigned_share - source_share)
        sample_value: Any = None if key[0] == "missing" else key[1]
        if key[0] == "int":
            sample_value = int(key[1])
        elif key[0] == "float":
            sample_value = float(key[1])
        rows.append(
            {
                "value": sample_value,
                "source_count": source_count,
                "assigned_count": assigned_count,
                "source_share": source_share,
                "assigned_share": assigned_share,
                "delta_percentage_points": delta_pp,
            }
        )
    return {
        "max_absolute_category_delta_percentage_points": max_delta_pp,
        "total_variation_distance": total_variation / 2,
        "categories": rows,
    }


def _compatibility_summary(mapped: pd.DataFrame) -> dict[str, Any]:
    n = len(mapped)
    age_rate = float(mapped["mapping_age_compatible"].mean())
    gender_rate = float(mapped["mapping_gender_compatible"].mean())
    both_rate = float(
        (mapped["mapping_age_compatible"] & mapped["mapping_gender_compatible"]).mean()
    )
    rationale_counts = mapped["mapping_rationale"].value_counts().sort_index()
    return {
        "age_compatible_count": int(mapped["mapping_age_compatible"].sum()),
        "age_compatible_share": age_rate,
        "gender_compatible_count": int(mapped["mapping_gender_compatible"].sum()),
        "gender_compatible_share": gender_rate,
        "both_compatible_count": int(
            (mapped["mapping_age_compatible"] & mapped["mapping_gender_compatible"]).sum()
        ),
        "both_compatible_share": both_rate,
        "mean_compatibility_score": float(mapped["mapping_compatibility_score"].mean()),
        "rationale_counts": {str(k): int(v) for k, v in rationale_counts.items()},
        "assigned_user_count": n,
    }


def create_synthetic_user_preferences(
    users: pd.DataFrame,
    survey: pd.DataFrame,
    seed: int = DEFAULT_MAPPING_SEED,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Expand all survey responses and assign them to users synthetically.

    Every raw survey response receives floor/ceil of the same expansion weight
    (8,000 / 520 for the current data). The global transportation assignment
    preserves those exact profile quotas while maximizing the total number of
    age-band and gender compatibility signals. Demographic mismatches remain
    permitted where required by the incompatible source margins.
    """
    missing_user = {"user_id", "age", "gender"} - set(users.columns)
    missing_survey = set([*DEMOGRAPHIC_COLUMNS, *PREFERENCE_COLUMNS]) - set(survey.columns)
    if missing_user or missing_survey:
        raise SyntheticMappingError(
            f"Missing required columns; users={sorted(missing_user)}, survey={sorted(missing_survey)}"
        )
    if users["user_id"].isna().any() or users["user_id"].duplicated().any():
        raise SyntheticMappingError("Users must have unique, non-null user_id values")
    if survey.empty or users.empty:
        raise SyntheticMappingError("Survey and user tables must both be non-empty")

    rng = np.random.default_rng(seed)
    quotas = _profile_quotas(len(survey), len(users), rng)
    user_groups_for_row: list[tuple[int, str]] = []
    normalized_user_genders: list[str] = []
    for row in users.itertuples(index=False):
        age = int(getattr(row, "age"))
        gender = _normalize_gender(getattr(row, "gender"))
        user_groups_for_row.append((age, gender))
        normalized_user_genders.append(gender)

    survey_groups_for_row: list[tuple[str, str]] = []
    survey_bands: dict[str, tuple[int, int | None]] = {}
    normalized_survey_genders: list[str] = []
    for age_value, gender_value in zip(survey["Age"], survey["Gender"]):
        age_label = str(age_value).strip()
        band = _parse_age_band(age_label)
        survey_bands[age_label] = band
        gender = _normalize_gender(gender_value)
        survey_groups_for_row.append((age_label, gender))
        normalized_survey_genders.append(gender)

    user_group_sizes = dict(Counter(user_groups_for_row))
    survey_group_sizes: dict[tuple[str, str], int] = defaultdict(int)
    for group, quota in zip(survey_groups_for_row, quotas):
        survey_group_sizes[group] += int(quota)
    survey_group_sizes = dict(survey_group_sizes)
    compatibility = {}
    for user_group in user_group_sizes:
        for survey_group in survey_group_sizes:
            compatibility[(user_group, survey_group)] = (
                _age_compatible(user_group[0], survey_bands[survey_group[0]]),
                user_group[1] == survey_group[1],
            )

    flow = _min_cost_transport(user_group_sizes, survey_group_sizes, compatibility, rng)

    users_by_group: dict[tuple[int, str], list[int]] = defaultdict(list)
    for row_index, group in enumerate(user_groups_for_row):
        users_by_group[group].append(row_index)
    survey_rows_by_group: dict[tuple[str, str], list[int]] = defaultdict(list)
    for response_index, group in enumerate(survey_groups_for_row):
        survey_rows_by_group[group].append(response_index)

    assigned_response = np.full(len(users), -1, dtype=np.int64)
    assigned_age_match = np.zeros(len(users), dtype=bool)
    assigned_gender_match = np.zeros(len(users), dtype=bool)
    target_users_by_survey_group: dict[tuple[str, str], list[int]] = defaultdict(list)
    for user_group in user_group_sizes:
        candidate_users = rng.permutation(np.asarray(users_by_group[user_group], dtype=np.int64))
        cursor = 0
        for survey_group in survey_group_sizes:
            count = flow.get((user_group, survey_group), 0)
            target_users_by_survey_group[survey_group].extend(
                candidate_users[cursor : cursor + count].tolist()
            )
            cursor += count
        if cursor != len(candidate_users):
            raise SyntheticMappingError(f"Internal user allocation mismatch for group {user_group}")

    for survey_group in survey_group_sizes:
        target_user_indices = target_users_by_survey_group[survey_group]
        response_tokens = np.concatenate(
            [np.repeat(response_index, quotas[response_index]) for response_index in survey_rows_by_group[survey_group]]
        )
        if len(target_user_indices) != len(response_tokens):
            raise SyntheticMappingError(f"Internal quota mismatch for survey demographic group {survey_group}")
        target_user_indices = rng.permutation(np.asarray(target_user_indices, dtype=np.int64)).tolist()
        response_tokens = rng.permutation(response_tokens)
        for user_index, response_index in zip(target_user_indices, response_tokens):
            assigned_response[user_index] = response_index
            age_match, gender_match = compatibility[(user_groups_for_row[user_index], survey_group)]
            assigned_age_match[user_index] = age_match
            assigned_gender_match[user_index] = gender_match

    if (assigned_response < 0).any():
        raise SyntheticMappingError("One or more users were not assigned a survey response")

    mapped = users[["user_id"]].reset_index(drop=True).copy()
    assigned_profiles = survey.iloc[assigned_response].reset_index(drop=True)
    mapped = pd.concat(
        [mapped, assigned_profiles[PREFERENCE_COLUMNS].copy()],
        axis=1,
    )
    mapped["source_response_row"] = assigned_response + 2  # spreadsheet row (header is row 1)
    mapped["mapping_age_compatible"] = assigned_age_match
    mapped["mapping_gender_compatible"] = assigned_gender_match
    mapped["mapping_compatibility_score"] = (
        assigned_age_match.astype(np.int8) + assigned_gender_match.astype(np.int8)
    )
    rationale = np.select(
        [assigned_age_match & assigned_gender_match, assigned_age_match, assigned_gender_match],
        ["age_and_gender_compatible", "age_only_compatible", "gender_only_compatible"],
        default="neither_demographic_signal_compatible",
    )
    mapped["mapping_rationale"] = rationale

    # Validate each profile's proportional expansion and every preference
    # attribute's resulting category distribution against all raw responses.
    observed_profile_counts = pd.Series(assigned_response).value_counts().reindex(
        range(len(survey)), fill_value=0
    ).to_numpy()
    if not np.array_equal(observed_profile_counts, quotas):
        raise SyntheticMappingError("Assigned profile counts do not match proportional source quotas")
    distributions = {
        column: _distribution_report(survey[column], mapped[column], len(mapped))
        for column in PREFERENCE_COLUMNS
    }
    for column, report in distributions.items():
        if report["max_absolute_category_delta_percentage_points"] > MAX_CATEGORY_DELTA_PP:
            raise SyntheticMappingError(
                f"{column}: category margin changed by more than {MAX_CATEGORY_DELTA_PP} percentage points"
            )
        if report["total_variation_distance"] > MAX_TOTAL_VARIATION:
            raise SyntheticMappingError(
                f"{column}: total variation exceeds {MAX_TOTAL_VARIATION:.1%}"
            )

    metadata = {
        "synthetic_linkage": True,
        "source_response_count": int(len(survey)),
        "assigned_user_count": int(len(users)),
        "seed": int(seed),
        "method": "proportional_response_expansion_with_global_demographic_compatibility_transport",
        "profile_quota_counts": {
            str(int(quota)): int(count) for quota, count in sorted(Counter(quotas.tolist()).items())
        },
        "demographic_scoring": {
            "score": "age_band_compatible (0/1) + normalized_gender_compatible (0/1)",
            "age_band_policy": "Survey ranges use inclusive endpoints as written; 60+ means age >= 60.",
            "gender_normalization": {"Others": "Other"},
            "constraints": "Soft only; global assignment maximizes total score while preserving profile quotas.",
            "tie_breaking": "Seeded integer costs are used only after compatibility score is prioritized.",
        },
        "compatibility": _compatibility_summary(mapped),
        "preference_distribution_comparison": distributions,
        "exact_duplicate_survey_rows_retained": int(survey.duplicated().sum()),
        "missing_source_preference_values": {
            column: int(survey[column].isna().sum()) for column in PREFERENCE_COLUMNS
        },
    }
    return mapped[["user_id", *PREFERENCE_COLUMNS, *MAPPING_COLUMNS]], metadata


def validate_synthetic_user_preferences(
    users: pd.DataFrame,
    survey: pd.DataFrame,
    mapped: pd.DataFrame,
    seed: int = DEFAULT_MAPPING_SEED,
) -> dict[str, Any]:
    """Validate keys, coverage, match diagnostics, nulls, and source margins."""
    expected_columns = ["user_id", *PREFERENCE_COLUMNS, *MAPPING_COLUMNS]
    if list(mapped.columns) != expected_columns:
        raise SyntheticMappingError(f"Unexpected user_preferences schema: {list(mapped.columns)}")
    if len(mapped) != len(users):
        raise SyntheticMappingError(f"Expected {len(users)} rows, got {len(mapped)}")
    if mapped["user_id"].isna().any() or mapped["user_id"].duplicated().any():
        raise SyntheticMappingError("user_preferences.user_id must be unique and non-null")
    if set(mapped["user_id"]) != set(users["user_id"]):
        raise SyntheticMappingError("user_preferences.user_id must cover exactly the users table")
    if mapped[MAPPING_COLUMNS].isna().any().any():
        raise SyntheticMappingError("Synthetic mapping metadata contains unexpected nulls")
    source_rows = mapped["source_response_row"].astype(int)
    response_indices = source_rows - 2
    if (response_indices < 0).any() or (response_indices >= len(survey)).any():
        raise SyntheticMappingError("source_response_row references an unknown survey response")

    user_lookup = users.set_index("user_id")[["age", "gender"]]
    joined = mapped.set_index("user_id").join(user_lookup, validate="one_to_one")
    ages = joined["age"].astype(int).to_numpy()
    user_genders = np.array([_normalize_gender(value) for value in joined["gender"]])
    source_profiles = survey.iloc[response_indices.to_numpy()]
    age_matches = np.array(
        [
            _age_compatible(int(age), _parse_age_band(band))
            for age, band in zip(ages, source_profiles["Age"])
        ],
        dtype=bool,
    )
    gender_matches = np.array(
        [
            user_gender == _normalize_gender(profile_gender)
            for user_gender, profile_gender in zip(user_genders, source_profiles["Gender"])
        ],
        dtype=bool,
    )
    if not np.array_equal(mapped["mapping_age_compatible"].to_numpy(dtype=bool), age_matches):
        raise SyntheticMappingError("mapping_age_compatible does not match source demographics")
    if not np.array_equal(mapped["mapping_gender_compatible"].to_numpy(dtype=bool), gender_matches):
        raise SyntheticMappingError("mapping_gender_compatible does not match source demographics")
    expected_scores = age_matches.astype(np.int8) + gender_matches.astype(np.int8)
    if not np.array_equal(mapped["mapping_compatibility_score"].to_numpy(dtype=int), expected_scores):
        raise SyntheticMappingError("mapping_compatibility_score is incorrect")
    expected_rationale = np.select(
        [age_matches & gender_matches, age_matches, gender_matches],
        ["age_and_gender_compatible", "age_only_compatible", "gender_only_compatible"],
        default="neither_demographic_signal_compatible",
    )
    if not np.array_equal(mapped["mapping_rationale"].astype(str).to_numpy(), expected_rationale):
        raise SyntheticMappingError("mapping_rationale is incorrect")

    # Structural survey missingness is allowed; extra nulls are not.
    profile_counts = response_indices.value_counts().to_dict()
    expected_nulls = {
        column: sum(
            count
            for response_index, count in profile_counts.items()
            if pd.isna(survey.iloc[int(response_index)][column])
        )
        for column in PREFERENCE_COLUMNS
    }
    distributions = {
        column: _distribution_report(survey[column], mapped[column], len(mapped))
        for column in PREFERENCE_COLUMNS
    }
    for column, report in distributions.items():
        if report["max_absolute_category_delta_percentage_points"] > MAX_CATEGORY_DELTA_PP:
            raise SyntheticMappingError(f"{column}: source category margin was not preserved")
        if report["total_variation_distance"] > MAX_TOTAL_VARIATION:
            raise SyntheticMappingError(f"{column}: source distribution was not preserved")
        if int(mapped[column].isna().sum()) != expected_nulls[column]:
            raise SyntheticMappingError(f"{column}: missing-value rate differs from proportional source expansion")

    summary = _compatibility_summary(mapped)
    return {
        "rows": len(mapped),
        "unique_user_ids": int(mapped["user_id"].nunique()),
        "age_compatible_share": summary["age_compatible_share"],
        "gender_compatible_share": summary["gender_compatible_share"],
        "both_compatible_share": summary["both_compatible_share"],
        "compatibility_score_counts": {
            str(int(score)): int(count)
            for score, count in mapped["mapping_compatibility_score"].value_counts().sort_index().items()
        },
        "maximum_category_delta_percentage_points": max(
            report["max_absolute_category_delta_percentage_points"]
            for report in distributions.values()
        ),
        "maximum_total_variation_distance": max(
            report["total_variation_distance"] for report in distributions.values()
        ),
        "validated_seed": int(seed),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_integration(
    seed: int = DEFAULT_MAPPING_SEED,
    raw_dir: Path | None = None,
    processed_dir: Path | None = None,
) -> dict[str, Any]:
    """Run Phase 1, integrate survey responses, validate, and write outputs."""
    raw_dir = Path(raw_dir) if raw_dir is not None else PROJECT_ROOT / "data" / "raw"
    processed_dir = Path(processed_dir) if processed_dir is not None else PROCESSED_DIR
    run_pipeline(raw_dir=raw_dir, processed_dir=processed_dir)
    users = pd.read_csv(processed_dir / "users.csv")
    survey = pd.read_excel(raw_dir / "spotify_user_preferences.xlsx")
    mapped, metadata = create_synthetic_user_preferences(users, survey, seed=seed)
    validation = validate_synthetic_user_preferences(users, survey, mapped, seed=seed)
    metadata["validation"] = validation
    metadata["input_sha256"] = {
        "spotify_user_preferences.xlsx": _sha256(raw_dir / "spotify_user_preferences.xlsx"),
        "users.csv": _sha256(processed_dir / "users.csv"),
    }

    output_path = processed_dir / "user_preferences.csv"
    metadata_path = processed_dir / "user_preferences_mapping_metadata.json"
    mapped.to_csv(output_path, index=False)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    # Re-read written artifacts to validate serialization and schema fidelity.
    written = pd.read_csv(output_path)
    validate_synthetic_user_preferences(users, survey, written, seed=seed)

    print("Phase 2 synthetic integration validation passed")
    print(f"Rows: {len(written):,}; source survey responses: {len(survey):,}; seed: {seed}")
    print("Demographic compatibility:")
    for key in ("age_compatible_share", "gender_compatible_share", "both_compatible_share"):
        print(f"- {key}: {validation[key]:.1%}")
    print("Preference category preservation:")
    for column, report in metadata["preference_distribution_comparison"].items():
        print(
            f"- {column}: max category delta "
            f"{report['max_absolute_category_delta_percentage_points']:.3f} pp; "
            f"TV distance {report['total_variation_distance']:.5f}"
        )
    return metadata


if __name__ == "__main__":
    run_integration()

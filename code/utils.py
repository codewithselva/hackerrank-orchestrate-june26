from __future__ import annotations
import csv
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

OUTPUT_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
]

CLAIM_STATUS_VALUES = ["supported", "contradicted", "not_enough_information"]
ISSUE_TYPE_VALUES = [
    "dent",
    "scratch",
    "crack",
    "glass_shatter",
    "broken_part",
    "missing_part",
    "torn_packaging",
    "crushed_packaging",
    "water_damage",
    "stain",
    "none",
    "unknown",
]

OBJECT_PART_VALUES = {
    "car": [
        "front_bumper",
        "rear_bumper",
        "door",
        "hood",
        "windshield",
        "side_mirror",
        "headlight",
        "taillight",
        "fender",
        "quarter_panel",
        "body",
        "unknown",
    ],
    "laptop": [
        "screen",
        "keyboard",
        "trackpad",
        "hinge",
        "lid",
        "corner",
        "port",
        "base",
        "body",
        "unknown",
    ],
    "package": [
        "box",
        "package_corner",
        "package_side",
        "seal",
        "label",
        "contents",
        "item",
        "unknown",
    ],
}

RISK_FLAG_VALUES = [
    "blurry_image",
    "cropped_or_obstructed",
    "low_light_or_glare",
    "wrong_angle",
    "wrong_object",
    "wrong_object_part",
    "damage_not_visible",
    "claim_mismatch",
    "possible_manipulation",
    "non_original_image",
    "text_instruction_present",
    "user_history_risk",
    "manual_review_required",
]

SEVERITY_VALUES = ["none", "low", "medium", "high", "unknown"]

TEXT_TRUE_VALUES = {"true", "1", "yes", "y", "t"}
TEXT_FALSE_VALUES = {"false", "0", "no", "n", "f"}


def load_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def write_csv_rows(path: str, rows: Sequence[Dict[str, str]], columns: Sequence[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def split_image_paths(image_path_value: str) -> List[str]:
    if image_path_value is None:
        return []
    return [entry.strip() for entry in str(image_path_value).split(";") if entry.strip()]


def image_id_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def normalize_image_path(image_path: str, base_path: Path) -> str:
    candidate = Path(image_path)
    if candidate.is_absolute():
        return str(candidate)
    return str((base_path / candidate).resolve())


def parse_boolean(value: Optional[str]) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    if text in TEXT_TRUE_VALUES:
        return True
    if text in TEXT_FALSE_VALUES:
        return False
    return False


def clean_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip()


def choose_enum(value: Optional[str], allowed: Sequence[str], default: str) -> str:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in allowed:
        return normalized
    return default


def semicolon_join(values: Iterable[str], none_value: str = "none") -> str:
    entries = [str(value).strip() for value in values if str(value).strip()]
    if not entries:
        return none_value
    return ";".join(entries)


def load_lookup_csv(path: str, key_field: str) -> Dict[str, Dict[str, str]]:
    rows = load_csv_rows(path)
    return {row[key_field]: row for row in rows if key_field in row}


def find_best_match(value: str, options: Sequence[str], fallback: str) -> str:
    if not value:
        return fallback
    normalized = value.strip().lower()
    for option in options:
        if normalized == option:
            return option
    for option in options:
        if option in normalized:
            return option
    return fallback


def extract_tokens(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", str(text).lower())

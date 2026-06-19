import pandas as pd
from pathlib import Path
from typing import List

OUTPUT_COLUMNS: List[str] = [
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


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(Path(path), dtype=str)


def write_output_csv(rows: List[dict], path: str) -> None:
    df = pd.DataFrame(rows)
    df = df.reindex(columns=OUTPUT_COLUMNS)
    df.to_csv(Path(path), index=False)

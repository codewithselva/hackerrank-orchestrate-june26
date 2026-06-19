import time
from pathlib import Path
from typing import Dict, List

from agent.evidence_checker import get_evidence_requirements, check_evidence_standard
from agent.history_loader import get_user_history, get_history_risk_flags
from agent.prompt_builder import build_prompt
from agent.vision_analyzer import analyze_claim
from utils.csv_io import OUTPUT_COLUMNS
from utils.image_utils import load_image_as_base64

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "dataset"


def process_claim(row: Dict[str, str], history_df, requirements_df) -> Dict[str, str]:
    user_id = row["user_id"]
    claim_object = row["claim_object"].lower()
    image_paths = row["image_paths"].split(";")
    image_contents: List[Dict[str, object]] = []
    image_reference: Dict[str, str] = {}

    for path in image_paths:
        path = path.strip()
        if not path:
            continue
        image_id = Path(path).stem
        image_reference[image_id] = path
        content = load_image_as_base64(str(DATA_DIR / path))
        if content is not None:
            image_contents.append(content)

    history = get_user_history(user_id, history_df)
    history_risk_flags = get_history_risk_flags(history)
    evidence_requirement = get_evidence_requirements(claim_object, "unknown", requirements_df)

    prompt = build_prompt(claim_object, row, history, evidence_requirement, image_reference)
    analysis = analyze_claim(prompt, image_contents)

    risk_flags = analysis.get("risk_flags", []) or []
    if isinstance(risk_flags, str):
        risk_flags = [risk_flags]
    merged_flags = set(risk_flags) | set(history_risk_flags)
    if not merged_flags:
        merged_flags = {"none"}

    supporting_image_ids = analysis.get("supporting_image_ids", []) or []
    if isinstance(supporting_image_ids, str):
        supporting_image_ids = [supporting_image_ids]
    supporting_images = ";".join([str(item) for item in supporting_image_ids]) if supporting_image_ids else "none"

    output = {
        "user_id": user_id,
        "image_paths": row["image_paths"],
        "user_claim": row["user_claim"],
        "claim_object": claim_object,
        "evidence_standard_met": str(analysis.get("evidence_standard_met", False)).lower(),
        "evidence_standard_met_reason": analysis.get("evidence_standard_met_reason", ""),
        "risk_flags": ";".join(sorted(merged_flags)) if merged_flags else "none",
        "issue_type": analysis.get("issue_type", "unknown"),
        "object_part": analysis.get("object_part", "unknown"),
        "claim_status": analysis.get("claim_status", "not_enough_information"),
        "claim_status_justification": analysis.get("claim_status_justification", ""),
        "supporting_image_ids": supporting_images,
        "valid_image": str(analysis.get("valid_image", False)).lower(),
        "severity": analysis.get("severity", "unknown"),
    }

    for key in OUTPUT_COLUMNS:
        output.setdefault(key, "")

    return output

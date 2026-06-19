from typing import Dict, List

ALLOWED_OBJECT_PARTS = {
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

ALLOWED_VALUES = {
    "issue_type": [
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
    ],
    "claim_status": ["supported", "contradicted", "not_enough_information"],
    "severity": ["none", "low", "medium", "high", "unknown"],
    "risk_flags": [
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
        "none",
    ],
}


def build_prompt(claim_object: str, claim_row: Dict[str, str], history_context: Dict[str, str], evidence_requirement: str, image_reference: Dict[str, str]) -> str:
    allowed_object_parts = ALLOWED_OBJECT_PARTS.get(claim_object.lower(), ALLOWED_OBJECT_PARTS["car"])
    prompt_lines: List[str] = [
        "You are a damage claim verification agent. Analyze the submitted images against the user's claim. Return only valid JSON, no markdown, no explanation outside the JSON.",
        "",
        "## Claim Details",
        f"Object type: {claim_object}",
        f"User conversation: {claim_row['user_claim']}",
        "",
        "## Evidence Requirements",
        evidence_requirement,
        "",
        "## User History Context",
        f"History summary: {history_context.get('history_summary', '')}",
        f"Past rejections: {history_context.get('rejected_claim', '0')}",
        "",
        "## Image Reference",
    ]

    for image_id, image_path in image_reference.items():
        prompt_lines.append(f"{image_id} → {image_path}")

    prompt_lines.extend([
        "",
        "## Your Task",
        "Inspect the images. Does the visual evidence support, contradict, or not provide enough information about the user's claim?",
        "",
        "Return ONLY a JSON object. No explanation outside the JSON.",
        "",
        "Allowed values:",
        f"issue_type: {ALLOWED_VALUES['issue_type']}",
        f"object_part: {allowed_object_parts}",
        f"claim_status: {ALLOWED_VALUES['claim_status']}",
        f"severity: {ALLOWED_VALUES['severity']}",
        f"risk_flags: {ALLOWED_VALUES['risk_flags']}",
        "evidence_standard_met: true | false",
        "valid_image: true | false",
        "",
        "Return JSON exactly in this shape:",
        "{",
        '  "issue_type": "...",',
        '  "object_part": "...",',
        '  "claim_status": "supported | contradicted | not_enough_information",',
        '  "claim_status_justification": "...",',
        '  "supporting_image_ids": ["img_1", "img_2"],',
        '  "valid_image": true,',
        '  "severity": "none | low | medium | high | unknown",',
        '  "risk_flags": ["blurry_image", "wrong_angle"],',
        '  "evidence_standard_met": true,',
        '  "evidence_standard_met_reason": "..."',
        "}",
    ])

    return "\n".join(prompt_lines)

from typing import List, Tuple

EVIDENCE_FAMILIES = {
    "dent": "dent or scratch",
    "scratch": "dent or scratch",
    "crack": "crack, broken, or missing part",
    "glass_shatter": "crack, broken, or missing part",
    "broken_part": "crack, broken, or missing part",
    "missing_part": "contents or inner item",
    "torn_packaging": "crushed, torn, or seal damage",
    "crushed_packaging": "crushed, torn, or seal damage",
    "water_damage": "water, stain, or label damage",
    "stain": "water, stain, or label damage",
    "none": "general claim review",
    "unknown": "general claim review",
}


def get_evidence_requirements(claim_object: str, issue_type: str, requirements_df) -> str:
    issue_family = EVIDENCE_FAMILIES.get(issue_type, "general claim review")
    rows = requirements_df[
        (requirements_df["claim_object"].str.lower() == claim_object.lower())
        | (requirements_df["claim_object"].str.lower() == "all")
    ]
    rows = rows[rows["applies_to"].str.lower().str.contains(issue_family.lower(), na=False)]
    if not rows.empty:
        return rows.iloc[0]["minimum_image_evidence"]
    rows = requirements_df[(requirements_df["claim_object"].str.lower() == claim_object.lower())]
    if not rows.empty:
        return rows.iloc[0]["minimum_image_evidence"]
    return "The claimed object and relevant part should be visible clearly enough to inspect the claimed condition."


def check_evidence_standard(image_count: int, requirements: str, image_flags: List[str]) -> Tuple[bool, str]:
    if image_count == 0:
        return False, "No images were provided."
    if any(flag in image_flags for flag in ["blurry_image", "cropped_or_obstructed", "low_light_or_glare", "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible"]):
        return False, "Image quality or relevance issues reduce evidence reliability."
    if image_count == 1 and "general claim review" not in requirements.lower():
        return True, requirements
    return True, requirements

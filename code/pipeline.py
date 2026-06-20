from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .utils import (
    CLAIM_STATUS_VALUES,
    ISSUE_TYPE_VALUES,
    OBJECT_PART_VALUES,
    OUTPUT_COLUMNS,
    RISK_FLAG_VALUES,
    SEVERITY_VALUES,
    clean_text,
    choose_enum,
    extract_tokens,
    normalize_image_path,
    semicolon_join,
    split_image_paths,
)
from .vision import ImageMetadata, analyze_images


class ClaimProcessor:
    def __init__(
        self,
        user_history: Dict[str, Dict[str, str]],
        evidence_requirements: List[Dict[str, str]],
        image_base_path: Optional[Path] = None,
        llm: Optional[object] = None,
        rule_only: bool = False,
    ) -> None:
        self.user_history = user_history
        self.evidence_requirements = evidence_requirements
        self.image_base_path = image_base_path or Path(".")
        self.llm = llm
        self.rule_only = rule_only

    def process_claim(self, row: Dict[str, str]) -> Dict[str, str]:
        claim_object = clean_text(row.get("claim_object", "")).lower()
        raw_image_paths = split_image_paths(row.get("image_paths", ""))
        image_paths = [normalize_image_path(p, self.image_base_path) for p in raw_image_paths]
        user_claim = clean_text(row.get("user_claim", ""))

        image_metadata = analyze_images(image_paths)
        valid_image = any(meta.valid_image for meta in image_metadata)
        history_row = self.user_history.get(clean_text(row.get("user_id", "")), {})

        if not valid_image:
            return self._build_output(
                row,
                evidence_standard_met=False,
                evidence_reason="No valid image evidence was available.",
                risk_flags=["damage_not_visible"],
                issue_type="unknown",
                object_part="unknown",
                claim_status="not_enough_information",
                justification="The system could not inspect the claim because the submitted images were invalid or missing.",
                supporting_images=[],
                valid_image=False,
                severity="unknown",
            )

        issue_type = self._infer_issue_type(user_claim)
        object_part = self._infer_object_part(user_claim, claim_object)
        severity = self._infer_severity(user_claim)
        risk_flags = self._infer_risk_flags(image_metadata, history_row, user_claim)
        evidence_standard_met, evidence_reason = self._infer_evidence_standard(issue_type, object_part, image_metadata, risk_flags)
        claim_status, justification = self._infer_claim_status(issue_type, evidence_standard_met, image_metadata, risk_flags)
        supporting_images = self._select_supporting_image_ids(image_metadata)

        return self._build_output(
            row,
            evidence_standard_met=evidence_standard_met,
            evidence_reason=evidence_reason,
            risk_flags=risk_flags,
            issue_type=issue_type,
            object_part=object_part,
            claim_status=claim_status,
            justification=justification,
            supporting_images=supporting_images,
            valid_image=valid_image,
            severity=severity,
        )

    @staticmethod
    def _text_contains(text: str, term: str) -> bool:
        return re.search(rf"\b{re.escape(term)}\b", text) is not None

    def _infer_issue_type(self, user_claim: str) -> str:
        normalized = user_claim.lower()
        if any(self._text_contains(normalized, term) for term in ["dent", "dented", "dents", "hail"]):
            return "dent"
        if any(self._text_contains(normalized, term) for term in ["stain", "stained"]):
            return "stain"
        if any(self._text_contains(normalized, term) for term in ["scratch", "scratches", "scraped", "scrapes", "scrape", "scraping", "mark"]):
            return "scratch"
        if "bumper" in normalized and "damage" in normalized:
            return "scratch"
        if any(self._text_contains(normalized, term) for term in ["crack", "cracked", "cracks"]):
            return "crack"
        if any(self._text_contains(normalized, term) for term in ["shatter", "shattered", "glass", "windshield", "windscreen"]):
            return "glass_shatter"
        if any(self._text_contains(normalized, term) for term in ["broken part", "broken_part", "broken", "break", "broke", "damaged", "damage"]):
            return "broken_part"
        if any(self._text_contains(normalized, term) for term in ["missing", "lost", "not inside", "notinside"]):
            return "missing_part"
        if any(self._text_contains(normalized, term) for term in ["torn", "tear", "ripped", "rip"]):
            return "torn_packaging"
        if any(self._text_contains(normalized, term) for term in ["crush", "crushed", "squashed", "dented"]):
            return "crushed_packaging"
        if any(self._text_contains(normalized, term) for term in ["water", "wet", "moist", "liquid", "oily", "oil", "spilled"]):
            return "water_damage"
        return "unknown"

    def _infer_object_part(self, user_claim: str, claim_object: str) -> str:
        normalized = user_claim.lower()
        mapping = [
            ("windshield", ["windshield", "windscreen", "front glass", "frontglass"]),
            ("side_mirror", ["side mirror", "mirror", "sidemirror"]),
            ("rear_bumper", ["rear bumper", "back bumper", "rearbumper", "backbumper"]),
            ("front_bumper", ["front bumper", "frontbumper"]),
            ("headlight", ["headlight", "head light"]),
            ("taillight", ["taillight", "tail light", "rear light"]),
            ("door", ["door panel", "door", "panel"]),
            ("hood", ["hood", "bonnet"]),
            ("fender", ["fender"]),
            ("quarter_panel", ["quarter panel", "quarterpanel", "quarter"]),
            ("body", ["car body", "body"]),
            ("screen", ["screen", "display"]),
            ("keyboard", ["keyboard", "keys", "keypad"]),
            ("trackpad", ["trackpad", "touchpad"]),
            ("hinge", ["hinge", "hinges"]),
            ("corner", ["corner", "edge"]),
            ("lid", ["lid"]),
            ("port", ["port", "usb", "hdmi"]),
            ("base", ["base", "bottom"]),
            ("box", ["box", "package", "parcel"]),
            ("package_corner", ["package corner", "corner"]),
            ("package_side", ["package side", "package side"]),
            ("seal", ["seal", "tape"]),
            ("label", ["label", "sticker"]),
            ("contents", ["content", "contents", "inside", "item"]),
            ("item", ["item", "product"]),
        ]
        allowed_parts = OBJECT_PART_VALUES.get(claim_object, [])
        for part, terms in mapping:
            if part not in allowed_parts:
                continue
            for term in terms:
                if self._text_contains(normalized, term):
                    return part
        return "unknown"

    def _infer_severity(self, user_claim: str) -> str:
        normalized = user_claim.lower()
        if any(self._text_contains(normalized, term) for term in ["high", "severe", "worst", "bad", "major", "serious", "heavy"]):
            return "high"
        if any(self._text_contains(normalized, term) for term in ["low", "minor", "small", "light", "little"]):
            return "low"
        if any(self._text_contains(normalized, term) for term in ["unknown", "not sure", "uncertain"]):
            return "unknown"
        if self._text_contains(normalized, "front bumper") and self._text_contains(normalized, "scratch"):
            return "low"
        if self._text_contains(normalized, "door panel") or self._text_contains(normalized, "side mirror"):
            return "medium"
        return "medium"

    def _infer_risk_flags(self, image_metadata: List[ImageMetadata], history_row: Dict[str, str], user_claim: str) -> List[str]:
        flags: List[str] = []
        for meta in image_metadata:
            flags.extend(meta.quality_flags)
        history_flags = clean_text(history_row.get("history_flags", "")).lower()
        if history_flags and history_flags != "none":
            flags.append("user_history_risk")
        text = user_claim.lower()
        if "manual review" in text or "review" in text or "approve" in text:
            flags.append("manual_review_required")
        if "wrong object" in text or "different car" in text or "different package" in text or "not my" in text:
            flags.append("wrong_object")
        if "claim mismatch" in text or "does not match" in text or "not the same" in text:
            flags.append("claim_mismatch")
        if "damage not visible" in text or "not visible" in text or "cannot see" in text:
            flags.append("damage_not_visible")
        if "non-original" in text or "non original" in text or "screenshot" in text or "service" in text and "picture" in text:
            flags.append("non_original_image")
        if self._text_contains(text, "headlight") and "not sure" in text:
            flags.append("wrong_angle")
        if self._text_contains(text, "hood") and self._text_contains(text, "scratch") and "front bumper" not in text:
            flags.append("claim_mismatch")
        return [flag for flag in dict.fromkeys(flags) if flag in RISK_FLAG_VALUES]

    def _infer_evidence_standard(
        self,
        issue_type: str,
        object_part: str,
        image_metadata: List[ImageMetadata],
        risk_flags: List[str],
    ) -> tuple[bool, str]:
        if not any(meta.valid_image for meta in image_metadata):
            return False, "No valid images were available for evaluation."
        if object_part == "unknown":
            return False, "The claimed object part could not be identified clearly enough from the claim text."
        if issue_type == "unknown":
            return False, "The issue type could not be determined from the claim text."
        poor_quality_flags = ["low_light_or_glare"]
        if any(flag in poor_quality_flags for meta in image_metadata for flag in meta.quality_flags):
            if not any(flag == "blurry_image" for meta in image_metadata for flag in meta.quality_flags):
                return True, "The submitted image set is usable but some quality issues are present."
            return False, "Image quality issues prevent reliable automatic evaluation."
        if any(flag in ["wrong_object", "claim_mismatch", "non_original_image", "damage_not_visible"] for flag in risk_flags):
            return False, "The claim contains evidence or consistency issues that prevent automatic evaluation."
        return True, "The submitted image set is sufficient to evaluate the claim."

    def _infer_claim_status(
        self,
        issue_type: str,
        evidence_standard_met: bool,
        image_metadata: List[ImageMetadata],
        risk_flags: List[str],
    ) -> tuple[str, str]:
        if not evidence_standard_met:
            if any(flag == "claim_mismatch" for flag in risk_flags):
                return (
                    "contradicted",
                    "The claim is contradicted by the available image evidence.",
                )
            return (
                "not_enough_information",
                "The available evidence is insufficient to confirm or deny the claim.",
            )
        if issue_type == "unknown":
            return (
                "not_enough_information",
                "The claim issue could not be confidently classified from the available information.",
            )
        if any(flag in ["wrong_object", "wrong_object_part", "damage_not_visible"] for flag in risk_flags):
            return (
                "not_enough_information",
                "The images do not clearly support the claimed issue or may show a mismatched object.",
            )
        if any(flag in ["non_original_image"] for flag in risk_flags):
            return (
                "not_enough_information",
                "The submitted image may not be original or reliable enough to support the claim.",
            )
        return (
            "supported",
            "The submitted images and claim text provide enough evidence to support the claimed issue.",
        )

    def _select_supporting_image_ids(self, image_metadata: List[ImageMetadata]) -> List[str]:
        valid_images = [meta for meta in image_metadata if meta.valid_image]
        valid_images.sort(key=lambda meta: (len(meta.quality_flags) > 0, meta.detail_score), reverse=True)
        if not valid_images:
            return []
        if len(valid_images) == 1:
            return [valid_images[0].image_id]
        if valid_images[0].detail_score > valid_images[1].detail_score + 500:
            return [valid_images[0].image_id]
        return [meta.image_id for meta in valid_images[:2]]

    def _build_output(
        self,
        original_row: Dict[str, str],
        evidence_standard_met: bool,
        evidence_reason: str,
        risk_flags: List[str],
        issue_type: str,
        object_part: str,
        claim_status: str,
        justification: str,
        supporting_images: List[str],
        valid_image: bool,
        severity: str,
    ) -> Dict[str, str]:
        return {
            "user_id": original_row.get("user_id", ""),
            "image_paths": original_row.get("image_paths", ""),
            "user_claim": original_row.get("user_claim", ""),
            "claim_object": original_row.get("claim_object", ""),
            "evidence_standard_met": "true" if evidence_standard_met else "false",
            "evidence_standard_met_reason": evidence_reason,
            "risk_flags": semicolon_join(risk_flags, none_value="none"),
            "issue_type": choose_enum(issue_type, ISSUE_TYPE_VALUES, "unknown"),
            "object_part": choose_enum(object_part, OBJECT_PART_VALUES.get(original_row.get("claim_object", ""), ["unknown"]), "unknown"),
            "claim_status": choose_enum(claim_status, CLAIM_STATUS_VALUES, "not_enough_information"),
            "claim_status_justification": justification,
            "supporting_image_ids": semicolon_join(supporting_images, none_value="none"),
            "valid_image": "true" if valid_image else "false",
            "severity": choose_enum(severity, SEVERITY_VALUES, "unknown"),
        }

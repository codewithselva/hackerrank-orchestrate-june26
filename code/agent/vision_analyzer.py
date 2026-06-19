import base64
import io
import json
import os
import time
from typing import List, Dict

try:
    import anthropic
except ImportError:
    anthropic = None

OPEN_CLIP_MODEL = "openai/clip-vit-base-patch32"
OPEN_NLI_MODEL = "facebook/bart-large-mnli"
ISSUE_TYPE_LABELS = [
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
CLAIM_STATUS_LABELS = ["supported", "contradicted", "not_enough_information"]
SEVERITY_LABELS = ["none", "low", "medium", "high", "unknown"]


def _load_open_source_modules():
    try:
        from transformers import CLIPProcessor, CLIPModel, pipeline
        import torch
        from PIL import Image
        return CLIPProcessor, CLIPModel, pipeline, torch, Image
    except Exception:
        return None, None, None, None, None


def _decode_base64_image(image_payload: dict):
    data = image_payload.get("source", {}).get("data")
    if not data:
        return None

    try:
        raw = base64.b64decode(data)
        from PIL import Image

        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def _compute_image_text_similarity(images: List[object], text: str):
    CLIPProcessor, CLIPModel, _, torch, _ = _load_open_source_modules()
    if CLIPProcessor is None or CLIPModel is None or torch is None:
        return []

    try:
        processor = CLIPProcessor.from_pretrained(OPEN_CLIP_MODEL)
        model = CLIPModel.from_pretrained(OPEN_CLIP_MODEL)
        inputs = processor(text=[text] * len(images), images=images, return_tensors="pt", padding=True)
        outputs = model(**inputs)
        image_embeds = outputs.image_embeds
        text_embeds = outputs.text_embeds
        text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)
        image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
        similarities = (image_embeds @ text_embeds.T).squeeze(-1)
        return [float(x.detach().cpu().item()) for x in similarities]
    except Exception:
        return []


def _zero_shot_classify(prompt: str, labels: List[str], default: str):
    _, _, pipeline_fn, _, _ = _load_open_source_modules()
    if pipeline_fn is None:
        return default

    try:
        classifier = pipeline_fn("zero-shot-classification", model=OPEN_NLI_MODEL)
        result = classifier(prompt, labels, multi_label=False)
        if isinstance(result, dict):
            return result.get("labels", [default])[0]
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("labels", [default])[0]
    except Exception:
        return default
    return default


def _keyword_extract_issue_type(prompt: str):
    normalized = prompt.lower()
    for issue in ISSUE_TYPE_LABELS:
        if issue.replace("_", " ") in normalized:
            return issue
    return "unknown"


def _keyword_extract_severity(prompt: str):
    normalized = prompt.lower()
    if any(word in normalized for word in ["severe", "major", "high"]):
        return "high"
    if any(word in normalized for word in ["moderate", "medium"]):
        return "medium"
    if any(word in normalized for word in ["light", "minor", "low"]):
        return "low"
    return "unknown"


def _build_fallback_analysis(prompt: str, image_contents: List[dict]) -> Dict[str, object]:
    images = [_decode_base64_image(item) for item in image_contents if item.get("type") == "image"]
    images = [img for img in images if img is not None]

    similarity_scores = _compute_image_text_similarity(images, prompt) if images else []
    valid_image = bool(similarity_scores and max(similarity_scores) >= 0.22)

    if not similarity_scores:
        claim_status = "not_enough_information"
    else:
        max_score = max(similarity_scores)
        if max_score >= 0.30:
            claim_status = "supported"
        elif max_score <= 0.18:
            claim_status = "contradicted"
        else:
            claim_status = "not_enough_information"

    supporting_image_ids = [
        f"img_{index + 1}"
        for index, score in enumerate(similarity_scores)
        if score >= 0.22
    ]

    issue_type = _zero_shot_classify(prompt, ISSUE_TYPE_LABELS, _keyword_extract_issue_type(prompt))
    severity = _keyword_extract_severity(prompt)
    risk_flags = []
    if not images:
        risk_flags.append("none")
    elif not valid_image:
        risk_flags.append("damage_not_visible")
    if claim_status == "contradicted" and images:
        risk_flags.append("wrong_object")

    return {
        "issue_type": issue_type,
        "object_part": "unknown",
        "claim_status": claim_status,
        "claim_status_justification": "Fallback open-source analyzer used because Anthropic access was unavailable.",
        "supporting_image_ids": supporting_image_ids,
        "valid_image": valid_image,
        "severity": severity,
        "risk_flags": risk_flags or ["none"],
        "evidence_standard_met": valid_image,
        "evidence_standard_met_reason": "Fallback open-source analysis applied." if valid_image else "No strong visual evidence found by the fallback analyzer.",
    }


def analyze_claim(prompt: str, image_contents: List[dict]) -> Dict[str, object]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic is not None and api_key:
        client = anthropic.Client(api_key=api_key)
        messages = [*image_contents, {"type": "text", "text": prompt}]

        def call_api():
            return client.messages.create(
                model="claude-sonnet-4-6",
                content=messages,
                max_tokens_to_sample=1024,
            )

        try:
            response = call_api()
        except Exception:
            time.sleep(5)
            try:
                response = call_api()
            except Exception:
                return _build_fallback_analysis(prompt, image_contents)

        text = ""
        if hasattr(response, "completion"):
            text = response.completion
        elif hasattr(response, "content"):
            content = response.content
            if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                text = content[0].get("text", "")
            elif isinstance(content, dict):
                text = content.get("text") or content.get("completion") or ""
            else:
                text = str(content)
        elif isinstance(response, dict):
            text = response.get("text") or response.get("completion") or response.get("content") or str(response)
        else:
            text = str(response)

        try:
            parsed = json.loads(text)
            return parsed
        except json.JSONDecodeError:
            return _build_fallback_analysis(prompt, image_contents)

    return _build_fallback_analysis(prompt, image_contents)

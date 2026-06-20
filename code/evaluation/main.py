from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, List, Sequence

from code.pipeline import ClaimProcessor
from code.utils import OUTPUT_COLUMNS, load_csv_rows, load_lookup_csv, write_csv_rows

EVALUATION_COLUMNS = [
    "evidence_standard_met",
    "issue_type",
    "object_part",
    "claim_status",
    "valid_image",
    "severity",
    "risk_flags",
    "supporting_image_ids",
]


def normalize_value(value: str) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def compare_rows(
    prediction: Dict[str, str],
    expected: Dict[str, str],
    columns: Sequence[str],
) -> Dict[str, bool]:
    return {
        column: normalize_value(prediction.get(column, ""))
        == normalize_value(expected.get(column, ""))
        for column in columns
    }


def build_evaluation_report(
    metrics: Dict[str, float],
    mismatch_examples: List[Dict[str, str]],
    total_rows: int,
) -> str:
    lines: List[str] = [
        "# Evaluation Report",
        "",
        "## Summary",
        f"Sample claims processed: {total_rows}",
        "",
        "## Metrics",
    ]

    for column, score in metrics.items():
        percent = round(score * 100, 1)
        lines.append(f"- {column}: {percent}% exact match")

    lines.extend(
        [
            "",
            "## Mismatch examples",
        ]
    )

    if not mismatch_examples:
        lines.append("No mismatches were found for the evaluated columns.")
    else:
        for example in mismatch_examples:
            lines.append("---")
            lines.append(f"User ID: {example['user_id']}")
            lines.append(f"Image paths: {example['image_paths']}")
            lines.append(f"Claim object: {example['claim_object']}")
            lines.append("Differences:")
            for diff in example["differences"]:
                lines.append(f"- {diff}")

    return "\n".join(lines)


def evaluate_sample() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    root = Path(__file__).resolve().parents[2]
    sample_path = root / "dataset" / "sample_claims.csv"
    history_path = root / "dataset" / "user_history.csv"
    requirements_path = root / "dataset" / "evidence_requirements.csv"
    predictions_path = root / "code" / "evaluation" / "sample_predictions.csv"
    report_path = root / "code" / "evaluation" / "evaluation_report.md"

    sample_rows = load_csv_rows(str(sample_path))
    user_history = load_lookup_csv(str(history_path), "user_id")
    requirements = load_csv_rows(str(requirements_path))
    processor = ClaimProcessor(
        user_history,
        requirements,
        image_base_path=sample_path.parent,
        llm=None,
        rule_only=True,
    )

    predictions = [processor.process_claim(row) for row in sample_rows]
    write_csv_rows(str(predictions_path), predictions, OUTPUT_COLUMNS)
    logging.info("Wrote sample predictions to %s", predictions_path)

    counts: Dict[str, int] = {column: 0 for column in EVALUATION_COLUMNS}
    mismatch_examples: List[Dict[str, str]] = []

    for prediction, expected in zip(predictions, sample_rows):
        comparison = compare_rows(prediction, expected, EVALUATION_COLUMNS)
        for column, matched in comparison.items():
            if matched:
                counts[column] += 1
        if not all(comparison.values()):
            differences = [
                f"{column}: expected={expected.get(column, '')!r}, predicted={prediction.get(column, '')!r}"
                for column, matched in comparison.items()
                if not matched
            ]
            if len(mismatch_examples) < 10:
                mismatch_examples.append(
                    {
                        "user_id": prediction.get("user_id", ""),
                        "image_paths": prediction.get("image_paths", ""),
                        "claim_object": prediction.get("claim_object", ""),
                        "differences": differences,
                    }
                )

    total_rows = len(sample_rows)
    metrics = {column: counts[column] / total_rows for column in EVALUATION_COLUMNS}
    report_text = build_evaluation_report(metrics, mismatch_examples, total_rows)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")
    logging.info("Wrote evaluation report to %s", report_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(evaluate_sample())

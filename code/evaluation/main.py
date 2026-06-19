import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "code"))

from agent.claim_processor import process_claim
from utils.csv_io import load_csv, OUTPUT_COLUMNS

DATA_DIR = REPO_ROOT / "dataset"
REPORT_PATH = REPO_ROOT / "code" / "evaluation" / "evaluation_report.md"
TEST_DATA_PATH = DATA_DIR / "claims.csv"
SAMPLE_DATA_PATH = DATA_DIR / "sample_claims.csv"
TOKEN_INPUT_PER_CALL = 1500
TOKEN_OUTPUT_PER_CALL = 300
INPUT_COST_PER_1K = 3.0
OUTPUT_COST_PER_1K = 15.0


def compare_predictions(predicted: dict, expected: dict) -> dict:
    return {
        "claim_status": predicted.get("claim_status") == expected.get("claim_status"),
        "issue_type": predicted.get("issue_type") == expected.get("issue_type"),
        "severity": predicted.get("severity") == expected.get("severity"),
        "evidence_standard_met": predicted.get("evidence_standard_met") == expected.get("evidence_standard_met"),
    }


def write_report(content: str) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(content, encoding="utf-8")


def main() -> None:
    sample_df = load_csv(str(SAMPLE_DATA_PATH))
    test_df = load_csv(str(TEST_DATA_PATH))
    history_df = load_csv(str(DATA_DIR / "user_history.csv"))
    requirements_df = load_csv(str(DATA_DIR / "evidence_requirements.csv"))
    history_df = history_df.set_index("user_id")

    predicted = []
    expected = []
    model_calls = 0
    start_time = time.perf_counter()

    for _, row in sample_df.iterrows():
        row_dict = row.to_dict()
        predicted_row = process_claim(row_dict, history_df, requirements_df)
        predicted.append(predicted_row)
        expected.append({col: row_dict.get(col, "") for col in OUTPUT_COLUMNS})
        model_calls += 1

    sample_model_calls = model_calls
    sample_rows = len(sample_df)
    test_rows = len(test_df)
    estimated_test_model_calls = test_rows
    estimated_test_input_tokens = estimated_test_model_calls * TOKEN_INPUT_PER_CALL
    estimated_test_output_tokens = estimated_test_model_calls * TOKEN_OUTPUT_PER_CALL
    estimated_test_cost = (
        estimated_test_input_tokens / 1000 * INPUT_COST_PER_1K
        + estimated_test_output_tokens / 1000 * OUTPUT_COST_PER_1K
    )

    duration = time.perf_counter() - start_time
    field_matches = {"claim_status": 0, "issue_type": 0, "severity": 0, "evidence_standard_met": 0}
    status_counts = Counter()
    confusion = Counter()
    images_processed = 0

    for pred, exp in zip(predicted, expected):
        comparison = compare_predictions(pred, exp)
        for field, match in comparison.items():
            if match:
                field_matches[field] += 1
        status_counts[exp["claim_status"]] += 1
        confusion[(exp["claim_status"], pred["claim_status"])] += 1
        images_processed += len([p for p in exp["image_paths"].split(";") if p.strip()])

    total = len(predicted)
    accuracies = {field: field_matches[field] / total for field in field_matches}

    report_lines = [
        "# Evaluation Report",
        "",
        "## Accuracy",
        f"Total sample rows: {total}",
        "",
        "| Field | Accuracy |",
        "|---|---|",
    ]
    for field in ["claim_status", "issue_type", "severity", "evidence_standard_met"]:
        report_lines.append(f"| {field} | {accuracies[field]:.2%} |")

    report_lines.extend([
        "",
        "## Claim Status Confusion Matrix",
        "",
        "| Expected \ Predicted | supported | contradicted | not_enough_information |",
        "|---|---|---|---|",
    ])

    statuses = ["supported", "contradicted", "not_enough_information"]
    for expected_status in statuses:
        row = [expected_status]
        for predicted_status in statuses:
            row.append(str(confusion[(expected_status, predicted_status)]))
        report_lines.append(f"| {' | '.join(row)} |")

    report_lines.extend([
        "",
        "## Operational Metrics",
        f"- Sample model calls: {sample_model_calls}",
        f"- Estimated sample input tokens: {sample_model_calls * TOKEN_INPUT_PER_CALL}",
        f"- Estimated sample output tokens: {sample_model_calls * TOKEN_OUTPUT_PER_CALL}",
        f"- Estimated sample cost: ${sample_model_calls * TOKEN_INPUT_PER_CALL / 1000 * INPUT_COST_PER_1K + sample_model_calls * TOKEN_OUTPUT_PER_CALL / 1000 * OUTPUT_COST_PER_1K:.2f}",
        f"- Estimated test model calls: {estimated_test_model_calls}",
        f"- Estimated test input tokens: {estimated_test_input_tokens}",
        f"- Estimated test output tokens: {estimated_test_output_tokens}",
        f"- Estimated test cost: ${estimated_test_cost:.2f}",
        f"- Images processed in sample: {images_processed}",
        f"- Runtime seconds (sample): {duration:.2f}",
        "- TPM/RPM considerations: sequential processing with a 0.5s delay in production to reduce the risk of Anthropic rate limit throttling.",
        "- Batching/caching: no batching is implemented yet; the system is designed to avoid unnecessary repeated calls by processing each claim once.",
        "- Retry strategy: one retry after a 5-second wait on API error.",
    ])

    write_report("\n".join(report_lines))
    print("Evaluation complete")
    print(f"Accuracy claim_status: {accuracies['claim_status']:.2%}")
    print(f"Accuracy issue_type: {accuracies['issue_type']:.2%}")
    print(f"Accuracy severity: {accuracies['severity']:.2%}")
    print(f"Accuracy evidence_standard_met: {accuracies['evidence_standard_met']:.2%}")


if __name__ == "__main__":
    main()

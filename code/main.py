import time
from pathlib import Path

from tqdm import tqdm

from agent.claim_processor import process_claim
from utils.csv_io import load_csv, write_output_csv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "dataset"
OUTPUT_CSV = BASE_DIR / "output.csv"


def main() -> None:
    claims_df = load_csv(str(DATA_DIR / "claims.csv"))
    history_df = load_csv(str(DATA_DIR / "user_history.csv"))
    requirements_df = load_csv(str(DATA_DIR / "evidence_requirements.csv"))
    history_df = history_df.set_index("user_id")

    results = []
    summary = {"supported": 0, "contradicted": 0, "not_enough_information": 0}

    for _, row in tqdm(claims_df.iterrows(), total=len(claims_df), desc="Processing claims"):
        result = process_claim(row.to_dict(), history_df, requirements_df)
        results.append(result)
        status = result.get("claim_status", "not_enough_information")
        if status in summary:
            summary[status] += 1
        time.sleep(0.5)

    write_output_csv(results, str(OUTPUT_CSV))
    print(f"Total processed: {len(results)}")
    print(f"supported: {summary['supported']}")
    print(f"contradicted: {summary['contradicted']}")
    print(f"not_enough_information: {summary['not_enough_information']}")


if __name__ == "__main__":
    main()

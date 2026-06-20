from __future__ import annotations
import argparse
import logging
import os
from pathlib import Path

from code.llm import LocalLLM
from code.pipeline import ClaimProcessor
from code.utils import OUTPUT_COLUMNS, load_csv_rows, load_lookup_csv, write_csv_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local damage claim evidence review.")
    parser.add_argument(
        "--input",
        default="dataset/claims.csv",
        help="Path to the claims CSV file.",
    )
    parser.add_argument(
        "--output",
        default="output.csv",
        help="Path to write the output CSV file.",
    )
    parser.add_argument(
        "--history",
        default="dataset/user_history.csv",
        help="Path to the user history CSV file.",
    )
    parser.add_argument(
        "--requirements",
        default="dataset/evidence_requirements.csv",
        help="Path to the evidence requirements CSV file.",
    )
    parser.add_argument(
        "--rule-only",
        action="store_true",
        help="Use only the rule-based inference path without invoking a local LLM.",
    )
    parser.add_argument(
        "--model-path",
        default="",
        help="Optional local model path for open-source LLM support.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent

    def resolve_path(value: str) -> Path:
        candidate = Path(value)
        return candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()

    input_path = resolve_path(args.input)
    output_path = resolve_path(args.output)
    history_path = resolve_path(args.history)
    requirements_path = resolve_path(args.requirements)

    logging.info("Loading claims from %s", input_path)
    claims = load_csv_rows(str(input_path))
    logging.info("Loading user history from %s", history_path)
    user_history = load_lookup_csv(str(history_path), "user_id")
    logging.info("Loading evidence requirements from %s", requirements_path)
    requirements = load_csv_rows(str(requirements_path))

    llm = None
    if args.model_path and not args.rule_only:
        try:
            llm = LocalLLM(args.model_path)
            if not llm.available():
                logging.warning("Local LLM model is unavailable. Falling back to rule-only mode.")
                llm = None
        except Exception as exc:
            logging.warning("Unable to initialize local LLM: %s", exc)
            llm = None

    processor = ClaimProcessor(
        user_history,
        requirements,
        image_base_path=input_path.parent,
        llm=llm,
        rule_only=args.rule_only,
    )
    outputs = [processor.process_claim(row) for row in claims]

    output_dir = output_path.parent
    os.makedirs(output_dir, exist_ok=True)
    write_csv_rows(str(output_path), outputs, OUTPUT_COLUMNS)
    logging.info("Wrote output to %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

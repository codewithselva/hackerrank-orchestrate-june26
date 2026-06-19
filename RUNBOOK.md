# Delivery Runbook for AMS Team

## Purpose
This runbook describes how to deploy, run, and validate the HackerRank Orchestrate damage claim verification agent for the AMS team.

## Repository Structure
- `AGENTS.md` — Challenge rules, delivery contract, and logging policy.
- `README.md` — High-level usage instructions for the project.
- `code/main.py` — Production entrypoint that processes `dataset/claims.csv` and writes `output.csv`.
- `code/evaluation/main.py` — Evaluation entrypoint that runs the system on `dataset/sample_claims.csv` and writes `code/evaluation/evaluation_report.md`.
- `code/agent/` — Core agent modules for history loading, evidence checking, prompt building, and Claude/Anthropic vision analysis.
- `code/utils/` — Helper modules for CSV I/O and image loading.
- `dataset/` — Input datasets and image assets.

## Pre-requisites
- Python 3.11+ recommended.
- Install dependencies from `code/requirements.txt`.
- Required environment variable: `ANTHROPIC_API_KEY`.

## Setup Steps
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd hackerrank-orchestrate-june26
   ```
2. Install dependencies:
   ```bash
   cd code
   pip install -r requirements.txt
   ```
3. Configure credentials:
   ```bash
   export ANTHROPIC_API_KEY="<your_anthropic_api_key>"
   ```
4. Confirm images and dataset files are present in `dataset/`.

## Run Instructions
### 1. Run the production agent
From the repo root:
```bash
python code/main.py
```
- Input: `dataset/claims.csv`
- Output: `output.csv`
- Behavior: sequential processing with a 0.5 second delay per claim to reduce API throttling risk.

### 2. Run evaluation
From the repo root:
```bash
python code/evaluation/main.py
```
- Input: `dataset/sample_claims.csv`
- Output: `code/evaluation/evaluation_report.md`
- Behavior: compares predicted outputs against sample ground truth and reports field-level accuracy.

## Key Delivery Notes
- The agent reads secrets only from environment variables.
- Image loading is based on dataset-relative paths and supports JPEG, PNG, WebP, and AVIF.
- The system is designed for deterministic execution where possible.
- The evaluation script also reports approximate model token usage and operational metrics.

## Validation Checklist
- [ ] `ANTHROPIC_API_KEY` is configured in environment.
- [ ] `python -m py_compile code/main.py code/evaluation/main.py` passes.
- [ ] `python code/main.py` completes and writes `output.csv`.
- [ ] `python code/evaluation/main.py` completes and writes `code/evaluation/evaluation_report.md`.
- [ ] Outputs contain the expected columns and no execution errors.

## Troubleshooting
- `ModuleNotFoundError: anthropic`: install `anthropic` using `pip install anthropic`.
- `FileNotFoundError` for dataset files: confirm `dataset/claims.csv`, `dataset/user_history.csv`, and `dataset/evidence_requirements.csv` exist.
- `ANTHROPIC_API_KEY` missing: export the variable before running.

## Handoff Summary
The AMS team should be able to deliver this agent by:
1. Installing dependencies.
2. Setting `ANTHROPIC_API_KEY`.
3. Running `python code/main.py` for production predictions.
4. Running `python code/evaluation/main.py` for sample evaluation.

For follow-up, refer to `AGENTS.md` for the project contract and `README.md` for more general usage details.

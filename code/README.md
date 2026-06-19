## Setup
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here

## Run evaluation (sample dataset)
python code/evaluation/main.py

## Run predictions (test dataset)
python code/main.py

## Output
output.csv is written to the repo root
evaluation/evaluation_report.md is written by the eval script

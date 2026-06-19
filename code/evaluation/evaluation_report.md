# Evaluation Report

## Accuracy
Total sample rows: 20

| Field | Accuracy |
|---|---|
| claim_status | 15.00% |
| issue_type | 15.00% |
| severity | 5.00% |
| evidence_standard_met | 15.00% |

## Claim Status Confusion Matrix

| Expected \ Predicted | supported | contradicted | not_enough_information |
|---|---|---|---|
| supported | 0 | 0 | 12 |
| contradicted | 0 | 0 | 5 |
| not_enough_information | 0 | 0 | 3 |

## Operational Metrics
- Sample model calls: 20
- Estimated sample input tokens: 30000
- Estimated sample output tokens: 6000
- Estimated sample cost: $180.00
- Estimated test model calls: 44
- Estimated test input tokens: 66000
- Estimated test output tokens: 13200
- Estimated test cost: $396.00
- Images processed in sample: 29
- Runtime seconds (sample): 1.13
- TPM/RPM considerations: sequential processing with a 0.5s delay in production to reduce the risk of Anthropic rate limit throttling.
- Batching/caching: no batching is implemented yet; the system is designed to avoid unnecessary repeated calls by processing each claim once.
- Retry strategy: one retry after a 5-second wait on API error.
# Final integration experiment

This folder contains one reproducible synthetic experiment for the Cloud vs Local Comparison.

- `final_cases.jsonl` is the labelled workload. Gold labels were fixed before inference.
- `synthetic_cloud_baseline.jsonl` is a controlled saved-response baseline. Its `latency_ms`
  values are synthetic test fixtures, not measurements from a real provider.
- The real local side uses the LM Studio model ID recorded in the final passport.

No cloud API was called. The baseline is intentionally mixed: it includes correct responses,
wrong fields, one invalid JSON response, and no claim of production safety.

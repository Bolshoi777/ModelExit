"""ModelExit — local-model migration-readiness test bench.

A small, honest MVP: run a bounded set of labelled customer-support tickets
through a locally served open-weight model (LM Studio, OpenAI-compatible API),
score the deterministic results against gold labels, surface the curated
Failure Frontier and export a transparent Exit Passport.
"""

__version__ = "0.1.0"

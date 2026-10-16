"""G3 — passport/export gate: valid JSON, measured counts, honest warnings.

The fake client below is a simulator that exists ONLY for unit tests; it is
never used by the app or the contest demo.
"""

import json

from modelexit.contracts import SupportCase
from modelexit.lm_client import ChatResult
from modelexit.passport import build_passport, passport_to_json, passport_to_markdown
from modelexit.runner import RunConfig, run_evaluation


class FakeLocalModel:
    """Unit-test simulator: returns canned raw responses keyed by case text."""

    def __init__(self, responses: dict[str, str]):
        self.responses = responses

    def chat_classify(self, model_id, ticket_text, temperature=0.0, max_tokens=160):
        return ChatResult(
            raw_text=self.responses[ticket_text],
            model_id=model_id,
            latency_ms=12,
            finish_reason="stop",
        )


def build_fixture_run():
    cases = [
        SupportCase.model_validate(
            {
                "id": "S01",
                "text": "invoice for order #4521 please",
                "expected": {"category": "billing", "priority": "low", "needs_human": False, "order_id": "4521"},
                "pair_id": "P01",
                "dimension": "original",
                "source": "synthetic",
            }
        ),
        SupportCase.model_validate(
            {
                "id": "S02",
                "text": "do not refund order #4521, just the invoice",
                "expected": {"category": "billing", "priority": "low", "needs_human": False, "order_id": "4521"},
                "pair_id": "P01",
                "dimension": "negation",
                "source": "synthetic",
            }
        ),
        SupportCase.model_validate(
            {
                "id": "S03",
                "text": "production outage right now",
                "expected": {"category": "technical", "priority": "high", "needs_human": True, "order_id": None},
                "pair_id": "P02",
                "dimension": "original",
                "source": "synthetic",
            }
        ),
    ]
    client = FakeLocalModel(
        {
            "invoice for order #4521 please": '{"category":"billing","priority":"low","needs_human":false,"order_id":"4521"}',
            "do not refund order #4521, just the invoice": '{"category":"billing","priority":"medium","needs_human":true,"order_id":null}',
            "production outage right now": "I cannot answer in JSON today, sorry.",
        }
    )
    return run_evaluation(
        cases,
        RunConfig(model_id="fake-model-for-tests", max_cases=3),
        dataset_name="tests/fixture",
        dataset_sha256="a" * 64,
        dataset_synthetic=True,
        client=client,
    )


def test_passport_json_roundtrip_and_counts():
    run = build_fixture_run()
    passport = build_passport(run)
    reparsed = json.loads(passport_to_json(passport))

    assert reparsed["schema_version"] == "1.0"
    assert reparsed["metrics"]["total_cases"] == run.metrics.total_cases == 3
    assert reparsed["metrics"]["exact_match"] == {"correct": 1, "total": 3, "rate": 1 / 3}
    assert reparsed["critical_miss_ids"] == ["S03"]
    assert reparsed["decision"]["status"] == run.decision.status


def test_passport_identifies_dataset_model_and_warnings():
    passport = build_passport(build_fixture_run())

    assert passport["dataset"]["sha256"] == "a" * 64
    assert passport["dataset"]["synthetic"] is True
    assert passport["inference"]["model_id_requested"] == "fake-model-for-tests"
    assert passport["inference"]["model_ids_reported"] == ["fake-model-for-tests"]
    assert any("synthetic" in warning for warning in passport["warnings"])
    assert passport["warnings"], "invalid/parse problems must surface as warnings"


def test_passport_markdown_is_meaningful():
    passport = build_passport(build_fixture_run())
    markdown = passport_to_markdown(passport)

    assert markdown.strip()
    assert passport["decision"]["status"] in markdown
    assert "fake-model-for-tests" in markdown
    assert "Failure Frontier" in markdown

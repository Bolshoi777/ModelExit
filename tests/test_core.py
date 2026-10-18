"""G1 — core deterministic gate (import / scoring / malformed output / decision).

Deliberately tiny: simple fixtures, no model and no network.
"""

import json

from modelexit.contracts import parse_model_output
from modelexit.dataset import DatasetError, load_csv_bytes, load_jsonl_bytes
from modelexit.decision import INSUFFICIENT, NOT_READY, READY, decide
from modelexit.evaluator import compute_metrics, evaluate_case


def make_case(case_id="S01", text="Please email me the invoice for order #4521.",
              category="billing", priority="low", needs_human=False, order_id="4521"):
    return {
        "id": case_id,
        "text": text,
        "expected": {
            "category": category,
            "priority": priority,
            "needs_human": needs_human,
            "order_id": order_id,
        },
        "pair_id": "P01",
        "dimension": "original",
        "source": "synthetic",
    }


def load_cases(*records):
    data = ("\n".join(json.dumps(record) for record in records)).encode("utf-8")
    return load_jsonl_bytes(data, name="fixture.jsonl", synthetic=True)


def test_jsonl_import_validates_labels():
    dataset = load_cases(make_case())
    assert dataset.case_count == 1 and dataset.synthetic is True
    case = dataset.cases[0]
    assert case.expected.category == "billing" and case.expected.order_id == "4521"

    bad = make_case(case_id="S02")
    bad["expected"]["priority"] = "urgent"
    try:
        load_cases(make_case(), bad)
        raise AssertionError("unknown priority must be rejected")
    except DatasetError as exc:
        assert "line 2" in str(exc)


def test_csv_import_parses_booleans_strictly():
    good = (
        "id,text,category,priority,needs_human,order_id\n"
        'S01,"Invoice for order #4521 please",billing,low,false,4521\n'
    ).encode("utf-8")
    assert load_csv_bytes(good, "fixture.csv").cases[0].expected.needs_human is False

    ambiguous = (
        "id,text,category,priority,needs_human\n"
        "S01,Hello,billing,low,maybe\n"
    ).encode("utf-8")
    try:
        load_csv_bytes(ambiguous, "fixture.csv")
        raise AssertionError("ambiguous booleans must be rejected")
    except DatasetError as exc:
        assert "line 2" in str(exc)


def test_correct_prediction_passes():
    case = load_cases(make_case()).cases[0]
    raw = '{"category":"billing","priority":"low","needs_human":false,"order_id":"4521"}'
    outcome = evaluate_case(case, raw, latency_ms=100, model_id="test-model")
    assert outcome.exact_match is True
    assert all(outcome.field_correct.values())
    metrics = compute_metrics([outcome])
    assert metrics.exact_matches == 1 and metrics.exact_match_rate == 1.0


def test_incorrect_high_priority_blocks_ready():
    case = load_cases(
        make_case(
            case_id="S03",
            text="Production checkout is down for every customer right now.",
            category="technical",
            priority="high",
            needs_human=True,
            order_id=None,
        )
    ).cases[0]
    raw = '{"category":"technical","priority":"low","needs_human":false,"order_id":null}'
    outcome = evaluate_case(case, raw, latency_ms=100, model_id="test-model")
    assert outcome.critical_miss is True and outcome.exact_match is False

    decision = decide(compute_metrics([outcome]), [outcome])
    assert decision.status == NOT_READY and "S03" in " ".join(decision.reasons)


def test_malformed_json_is_a_recorded_failure():
    case = load_cases(make_case()).cases[0]
    outcome = evaluate_case(case, "BANANA 42", latency_ms=50, model_id="test-model")
    assert outcome.parse_error is not None
    assert outcome.exact_match is False and outcome.predicted is None

    parsed = parse_model_output('prose first {"category":"billing","priority":"low",'
                                '"needs_human":false,"order_id":"4521"} trailing prose')
    assert parsed.ok is True and parsed.parse_mode == "extracted"

    metrics = compute_metrics([outcome])
    assert metrics.invalid_responses == 1
    # A small broken run is INSUFFICIENT EVIDENCE (never a fake pass) and says so:
    decision = decide(metrics, [outcome])
    assert decision.status == INSUFFICIENT
    assert "invalid" in " ".join(decision.reasons).lower()

    # Malformed output on a CRITICAL case blocks readiness outright:
    critical_case = load_cases(
        make_case(
            case_id="S03",
            text="Production checkout is down for every customer right now.",
            category="technical",
            priority="high",
            needs_human=True,
            order_id=None,
        )
    ).cases[0]
    critical_outcome = evaluate_case(critical_case, "not json at all", latency_ms=40, model_id="test-model")
    assert critical_outcome.critical_miss is True
    assert decide(compute_metrics([critical_outcome]), [critical_outcome]).status == NOT_READY


def test_zero_denominators_do_not_divide_by_zero():
    case = load_cases(make_case()).cases[0]  # gold priority=low, needs_human=false
    outcome = evaluate_case(
        case,
        '{"category":"billing","priority":"low","needs_human":false,"order_id":"4521"}',
        latency_ms=10,
        model_id="test-model",
    )
    metrics = compute_metrics([outcome])
    assert metrics.high_priority_recall is None  # N/A, no gold-high cases
    assert metrics.needs_human_recall is None
    assert metrics.exact_match_rate == 1.0
    assert decide(metrics, [outcome]).status == INSUFFICIENT  # 1 case < 10

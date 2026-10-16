"""ModelExit — Streamlit UI in three sections: Run, Failures, Passport.

Run inference ONLY from an explicit button click; the complete RunRecord is
stored in session state so widget rerenders never repeat the batch. All data
stays in this local process; nothing is uploaded (except LM Studio on
loopback).
"""

from __future__ import annotations

import json

import streamlit as st

from modelexit.dataset import (
    DEFAULT_EVAL_CASES,
    SMALL_EVAL_CASES,
    Dataset,
    DatasetError,
    load_bundled_sample,
    load_dataset_bytes,
    bound_cases,
)
from modelexit.frontier import build_frontier, frontier_summary
from modelexit.lm_client import DEFAULT_BASE_URL, LMStudioClient, LMStudioError
from modelexit.passport import build_passport, passport_to_json, passport_to_markdown
from modelexit.runner import RunConfig, RunRecord, run_evaluation

st.set_page_config(page_title="ModelExit", page_icon="🚪", layout="wide")

STATUS_RENDER = {
    "READY FOR LIMITED PILOT": ("success", "✅"),
    "NOT READY": ("error", "⛔"),
    "INSUFFICIENT EVIDENCE": ("warning", "❔"),
    "NEEDS REVIEW": ("warning", "⚠️"),
}


def init_state() -> None:
    defaults = {
        "models": None,
        "models_error": None,
        "models_base_url": None,
        "base_url_input": DEFAULT_BASE_URL,
        "dataset": None,
        "uploaded_fingerprint": None,
        "report": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def current_model_id() -> str:
    models = st.session_state.get("models")
    if models:
        return st.session_state.get("model_choice") or models[0]
    return (st.session_state.get("manual_model") or "").strip()


def show_decision_badge(status: str) -> None:
    kind, icon = STATUS_RENDER.get(status, ("info", "ℹ️"))
    renderer = {"success": st.success, "error": st.error, "warning": st.warning, "info": st.info}[kind]
    renderer(f"{icon} **{status}**")


# --------------------------------------------------------------------------
# Run tab
# --------------------------------------------------------------------------

def render_connection_section() -> None:
    st.subheader("1 · Local model connection")
    st.caption(
        "ModelExit talks only to a loopback LM Studio server (OpenAI-compatible). "
        "No cloud APIs, no keys, nothing leaves this machine."
    )
    col_url, col_button = st.columns([4, 1], vertical_alignment="bottom")
    base_url = col_url.text_input(
        "LM Studio base URL",
        key="base_url_input",
        help="Default: http://127.0.0.1:1234/v1 (LM Studio → Developer → Start Server).",
    )
    if col_button.button("Check connection", width="stretch"):
        try:
            client = LMStudioClient(base_url)
            models = client.list_models()
            st.session_state.models = [m.id for m in models]
            st.session_state.models_error = None
            st.session_state.models_base_url = base_url
        except LMStudioError as exc:
            st.session_state.models = None
            st.session_state.models_error = f"[{exc.kind}] {exc.message}"
            st.session_state.models_base_url = base_url

    models = st.session_state.get("models")
    error = st.session_state.get("models_error")
    if models:
        st.success(f"Connected — {len(models)} model(s) available at {st.session_state.models_base_url}")
        st.selectbox("Model id reported by GET /v1/models", options=models, key="model_choice")
    elif error:
        st.error(f"Connection problem:\n\n{error}")
        st.text_input(
            "Manual model id (optional, only if you know a loaded model id)",
            key="manual_model",
            placeholder="e.g. the exact id shown in LM Studio",
        )
    else:
        st.info("Not checked yet. Start LM Studio, load a model, then click **Check connection**.")
        st.text_input(
            "Manual model id (optional)",
            key="manual_model",
            placeholder="Leave empty until connection succeeds",
        )


def render_dataset_section() -> None:
    st.subheader("2 · Evaluation cases")
    source = st.radio(
        "Case source",
        ["Bundled synthetic sample", "Upload CSV / JSONL"],
        horizontal=True,
        key="dataset_source",
    )

    if source == "Bundled synthetic sample":
        st.caption(
            "12 curated synthetic support tickets (visibly synthetic fixtures, not real customers), "
            "including paired edge cases for the Failure Frontier."
        )
        if st.button("Load bundled sample"):
            dataset = load_bundled_sample()
            st.session_state.dataset = dataset
            st.session_state.report = None
    else:
        uploaded = st.file_uploader("Upload CSV or JSONL (max 24 cases)", type=["csv", "jsonl", "ndjson"])
        if uploaded is not None:
            fingerprint = f"{uploaded.name}:{uploaded.size}"
            if st.session_state.get("uploaded_fingerprint") != fingerprint:
                try:
                    data = uploaded.getvalue()
                    dataset = load_dataset_bytes(data, name=uploaded.name, synthetic=False)
                    st.session_state.dataset = dataset
                    st.session_state.uploaded_fingerprint = fingerprint
                    st.session_state.report = None
                except DatasetError as exc:
                    st.error(f"Dataset rejected:\n\n{exc}")
                    st.session_state.dataset = None
                    st.session_state.uploaded_fingerprint = fingerprint

    dataset: Dataset | None = st.session_state.get("dataset")
    if dataset is not None:
        label = "synthetic fixture" if dataset.synthetic else "user-provided labels (not declared synthetic)"
        st.markdown(
            f"**Loaded:** `{dataset.name}` — {dataset.case_count} cases · SHA-256 "
            f"`{dataset.sha256[:16]}…` · {label}"
        )
        with st.expander("Preview cases and gold labels", expanded=False):
            st.dataframe(
                [
                    {
                        "id": case.id,
                        "pair": case.pair_id or "",
                        "dimension": case.dimension or "",
                        "text": case.text,
                        "category": case.expected.category,
                        "priority": case.expected.priority,
                        "needs_human": case.expected.needs_human,
                        "order_id": case.expected.order_id,
                    }
                    for case in dataset.cases
                ],
                width="stretch",
                hide_index=True,
            )


def render_run_section() -> None:
    st.subheader("3 · Run local evaluation")
    dataset: Dataset | None = st.session_state.get("dataset")
    model_id = current_model_id()

    col_cases, col_info = st.columns([1, 3])
    max_cases = col_cases.selectbox(
        "Cases to evaluate",
        options=[SMALL_EVAL_CASES, DEFAULT_EVAL_CASES],
        index=1,
        format_func=lambda n: f"{n} cases",
        key="max_cases",
    )
    if dataset is not None and dataset.case_count < max_cases:
        max_cases = dataset.case_count
    col_info.caption(
        "Bounded run: serial calls, max 12 cases, 25 s per call, no automatic retries. "
        "A dead server stops the run after 3 consecutive failures."
    )

    ready = dataset is not None and bool(model_id)
    if not ready:
        missing = []
        if dataset is None:
            missing.append("load cases")
        if not model_id:
            missing.append("select a model (check connection first)")
        st.info("To enable the run button: " + "; ".join(missing) + ".")

    if st.button("▶ Run Local Evaluation", type="primary", disabled=not ready):
        cases = bound_cases(dataset.cases, max_cases)
        config = RunConfig(
            base_url=st.session_state.get("base_url_input") or DEFAULT_BASE_URL,
            model_id=model_id,
            max_cases=max_cases,
        )
        progress = st.progress(0.0, text="Starting…")
        status_line = st.empty()

        def on_progress(done: int, total: int, outcome) -> None:
            progress.progress(done / total, text=f"{done}/{total} cases evaluated")
            verdict = "PASS" if outcome.exact_match else ("INVALID" if outcome.invalid else "FAIL")
            status_line.caption(f"Last: `{outcome.case.id}` → {verdict} · {outcome.latency_ms} ms")

        try:
            report = run_evaluation(
                cases,
                config,
                dataset_name=dataset.name,
                dataset_sha256=dataset.sha256,
                dataset_synthetic=dataset.synthetic,
                progress_callback=on_progress,
            )
        except LMStudioError as exc:
            st.error(f"Configuration problem: [{exc.kind}] {exc.message}")
        else:
            st.session_state.report = report
            progress.progress(1.0, text="Run finished")
            status_line.empty()
            st.divider()
            show_decision_badge(report.decision.status)
            m = report.metrics
            cols = st.columns(4)
            cols[0].metric("Exact match", f"{m.exact_matches}/{m.total_cases}")
            cols[1].metric(
                "High-priority recall",
                "N/A" if m.high_priority_recall is None else f"{m.high_priority_recall:.0%}",
                help=f"gold-high cases: {m.gold_high_count}",
            )
            cols[2].metric("Critical misses", len(m.critical_miss_ids))
            cols[3].metric("Invalid responses", m.invalid_responses)
            st.caption(
                f"Run `{report.run_id}` · {report.status} · elapsed {report.elapsed_s:.1f}s · "
                f"model `{report.config.model_id}` — see **Failures** and **Passport** tabs."
            )

    report: RunRecord | None = st.session_state.get("report")
    if report is not None:
        st.caption(
            "A finished run is stored in this session; changing widgets does not re-run the model. "
            "Click the button again only for a deliberate new run."
        )


# --------------------------------------------------------------------------
# Failures tab
# --------------------------------------------------------------------------

def render_failures_tab() -> None:
    report: RunRecord | None = st.session_state.get("report")
    if report is None:
        st.info("No run yet — start one in the **Run** tab.")
        return

    metrics = report.metrics
    st.subheader("Measured metrics (denominators shown)")

    cols = st.columns(5)
    cols[0].metric("Exact match", f"{metrics.exact_matches}/{metrics.total_cases}")
    cols[1].metric("Invalid responses", f"{metrics.invalid_responses}/{metrics.total_cases}")
    cols[2].metric(
        "High-priority recall",
        "N/A" if metrics.high_priority_recall is None else f"{metrics.high_priority_recall:.0%}",
        help=f"correct / {metrics.gold_high_count} gold-high cases",
    )
    cols[3].metric(
        "needs_human recall",
        "N/A" if metrics.needs_human_recall is None else f"{metrics.needs_human_recall:.0%}",
        help=f"correct / {metrics.gold_needs_human_count} gold needs_human cases",
    )
    cols[4].metric("Critical cases passed", f"{metrics.critical_pass_count}/{metrics.critical_case_count}")

    with st.expander("Field accuracy (correct / all cases, including errors)"):
        st.dataframe(
            [
                {
                    "field": field,
                    "correct": metrics.field_correct_counts.get(field, 0),
                    "total": metrics.total_cases,
                    "accuracy": (
                        "N/A"
                        if metrics.field_accuracy.get(field) is None
                        else f"{metrics.field_accuracy[field]:.0%}"
                    ),
                }
                for field in ("category", "priority", "needs_human", "order_id")
            ],
            hide_index=True,
            width="stretch",
        )

    st.subheader("Per-case outcomes")
    st.dataframe(
        [
            {
                "id": o.case.id,
                "pair": o.case.pair_id or "",
                "dimension": o.case.dimension or "",
                "exact": "PASS" if o.exact_match else ("INVALID" if o.invalid else "FAIL"),
                "category ✓": o.field_correct["category"],
                "priority ✓": o.field_correct["priority"],
                "needs_human ✓": o.field_correct["needs_human"],
                "order_id ✓": o.field_correct["order_id"],
                "critical": o.critical,
                "critical miss": o.critical_miss,
                "latency_ms": o.latency_ms,
                "error": (
                    o.inference_error.message
                    if o.inference_error
                    else (o.parse_error or "")
                ),
            }
            for o in report.outcomes
        ],
        width="stretch",
        hide_index=True,
    )

    with st.expander("Single-case details (expected vs actual, raw response)"):
        case_ids = [o.case.id for o in report.outcomes]
        chosen = st.selectbox("Case", case_ids, key=f"detail_case_{report.run_id}")
        outcome = next(o for o in report.outcomes if o.case.id == chosen)
        left, right = st.columns(2)
        left.markdown("**Gold label (from dataset)**")
        left.json(outcome.case.expected.model_dump())
        right.markdown("**Model prediction (parsed)**")
        right.json(outcome.predicted.model_dump() if outcome.predicted else None)
        st.caption(
            f"parse mode: {outcome.parse_mode} · latency: {outcome.latency_ms} ms · "
            f"model reported: `{outcome.model_id}`"
        )
        if outcome.inference_error:
            st.error(f"Inference error [{outcome.inference_error.kind}]: {outcome.inference_error.message}")
        if outcome.parse_error:
            st.warning(f"Parse error: {outcome.parse_error}")
        st.markdown("**Raw response (truncated for export)**")
        st.code(outcome.raw_response or "(none — the call failed)", language="json")

    st.subheader("Failure Frontier — curated paired cases")
    frontier = build_frontier(report.outcomes)
    if not frontier:
        st.info("This dataset has no pair_id grouped cases.")
    else:
        summary = frontier_summary(frontier)
        st.caption(
            "Curated counterfactual pairs that were actually evaluated (original vs one controlled "
            "meaning change). This is not an automatic discovery of every failure mode. "
            + " · ".join(f"{label}: {count}" for label, count in sorted(summary.items()))
        )
        for pair in frontier:
            heading = {
                "regression": "🔴 regression",
                "both_fail": "🟠 both fail",
                "stable_pass": "🟢 stable pass",
                "improvement": "🔵 improvement",
            }.get(pair.label, f"⚪ {pair.label}")
            with st.container(border=True):
                st.markdown(f"**Pair `{pair.pair_id}` — {heading}**")
                if pair.original is not None:
                    original = pair.original
                    st.markdown(
                        f"- **Original** `{original.case_id}` ({original.dimension or '—'}): "
                        f"{'PASS' if original.exact_match else ('INVALID' if original.invalid else 'FAIL')} — "
                        f"“{original.text}”"
                    )
                    if original.invalid:
                        st.caption(f"  ⚠ {original.error}")
                for side in pair.changed:
                    st.markdown(
                        f"- **Changed** `{side.case_id}` ({side.dimension or '—'}): "
                        f"{'PASS' if side.exact_match else ('INVALID' if side.invalid else 'FAIL')} — "
                        f"“{side.text}”"
                    )
                    if side.invalid:
                        st.caption(f"  ⚠ {side.error}")
                st.caption(pair.note)


# --------------------------------------------------------------------------
# Passport tab
# --------------------------------------------------------------------------

def render_passport_tab() -> None:
    report: RunRecord | None = st.session_state.get("report")
    if report is None:
        st.info("No run yet — the Exit Passport is generated from a finished run in the **Run** tab.")
        return

    passport = build_passport(report)
    decision = passport["decision"]

    show_decision_badge(decision["status"])
    for reason in decision["reasons"]:
        st.markdown(f"- {reason}")
    with st.expander("Readiness rule (transparent heuristic)"):
        st.write(decision["rule"])

    st.divider()
    meta_cols = st.columns(3)
    meta_cols[0].markdown(
        f"**Dataset**\n\n`{passport['dataset']['name']}`\n\n"
        f"- cases evaluated: {passport['dataset']['case_count_evaluated']} / "
        f"{passport['dataset']['case_count_requested']}\n"
        f"- synthetic: {'yes' if passport['dataset']['synthetic'] else 'no / not declared'}\n"
        f"- sha256: `{passport['dataset']['sha256'][:20]}…`"
    )
    reported_models = passport["inference"]["model_ids_reported"] or ["(none)"]
    meta_cols[1].markdown(
        f"**Model (reported by server)**\n\n"
        + "\n".join(f"- `{m}`" for m in reported_models)
        + f"\n\n- temperature: {passport['inference']['temperature']}\n"
        f"- max_tokens: {passport['inference']['max_tokens']}\n"
        f"- timeout: {passport['inference']['timeout_s_per_call']} s per call"
    )
    meta_cols[2].markdown(
        f"**Run**\n\n- id: `{passport['run_id']}`\n- created (UTC): {passport['created_at_utc']}\n"
        f"- status: {passport['run_status']}\n- elapsed: {passport['metrics']['run_elapsed_s']} s\n"
        f"- calls succeeded: {passport['inference']['calls_succeeded']}/"
        f"{passport['inference']['calls_total']}"
    )

    warnings = passport["warnings"]
    if warnings:
        st.subheader("Warnings")
        for warning in warnings:
            st.warning(warning)

    st.subheader("Limitations (shipped with every passport)")
    for limitation in passport["limitations"]:
        st.markdown(f"- {limitation}")

    st.divider()
    json_text = passport_to_json(passport)
    markdown_text = passport_to_markdown(passport)
    col_json, col_md = st.columns(2)
    col_json.download_button(
        "⬇ Download Exit Passport (JSON)",
        data=json_text,
        file_name=f"modelexit_passport_{report.run_id}.json",
        mime="application/json",
        width="stretch",
    )
    col_md.download_button(
        "⬇ Download Exit Passport (Markdown)",
        data=markdown_text,
        file_name=f"modelexit_passport_{report.run_id}.md",
        mime="text/markdown",
        width="stretch",
    )
    with st.expander("Preview Markdown passport"):
        st.markdown(markdown_text)


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

def main() -> None:
    init_state()
    st.title("🚪 ModelExit")
    st.caption(
        "Know where your app can safely leave paid AI behind. A local open-weight model is "
        "evaluated against your labelled support-ticket cases; the Exit Passport reports what "
        "passed, what failed and what still needs human review. Synthetic fixtures are labelled; "
        "no data leaves your machine."
    )

    tab_run, tab_failures, tab_passport = st.tabs(["Run", "Failures", "Passport"])
    with tab_run:
        render_connection_section()
        st.divider()
        render_dataset_section()
        st.divider()
        render_run_section()
    with tab_failures:
        render_failures_tab()
    with tab_passport:
        render_passport_tab()


main()

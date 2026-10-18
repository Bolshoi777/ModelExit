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
    sha256_hex,
)
from modelexit.comparison import (
    CloudBaseline,
    ComparisonError,
    ComparisonReport,
    compare_run,
    load_baseline_bytes,
)
from modelexit.frontier import build_frontier, frontier_summary
from modelexit.lm_client import DEFAULT_BASE_URL, LMStudioClient, LMStudioError
from modelexit.passport import build_passport, passport_to_json, passport_to_markdown
from modelexit.runner import RunConfig, RunRecord, run_evaluation

st.set_page_config(page_title="ModelExit", page_icon="🚪", layout="wide")

STATUS_RENDER = {
    "READY FOR LIMITED PILOT": ("success", "READY FOR LIMITED PILOT"),
    "NOT READY": ("error", "NOT READY"),
    "INSUFFICIENT EVIDENCE": ("warning", "INSUFFICIENT EVIDENCE"),
    "NEEDS REVIEW": ("warning", "NEEDS REVIEW"),
}


def init_state() -> None:
    defaults = {
        "models": None,
        "models_error": None,
        "models_base_url": None,
        "base_url_input": DEFAULT_BASE_URL,
        "dataset": None,
        "uploaded_fingerprint": None,
        "cloud_baseline": None,
        "cloud_baseline_fingerprint": None,
        "cloud_baseline_error": None,
        "comparison": None,
        "report": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def current_model_id() -> str:
    models = st.session_state.get("models")
    if models and st.session_state.get("models_base_url") == st.session_state.get("base_url_input"):
        return st.session_state.get("model_choice") or models[0]
    return (st.session_state.get("manual_model") or "").strip()


def show_decision_badge(status: str) -> None:
    kind, label = STATUS_RENDER.get(status, ("info", status))
    renderer = {"success": st.success, "error": st.error, "warning": st.warning, "info": st.info}[kind]
    renderer(f"**{label}**")


def apply_styles() -> None:
    """Small, restrained visual system for a readable local workbench."""
    st.markdown(
        """
        <style>
        :root { --mx-ink: #172033; --mx-muted: #5c667a; --mx-line: #dfe5ee; --mx-blue: #3157c8; }
        .stApp { background: #f5f7fb; color: var(--mx-ink); }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stAppViewContainer"] > .main > div { max-width: 1180px; padding-top: 2.25rem; }
        h1 { letter-spacing: -0.04em; font-weight: 760; color: var(--mx-ink); margin-bottom: 0.15rem; }
        h2, h3 { letter-spacing: -0.02em; color: var(--mx-ink); }
        h2 { margin-top: 1.2rem; }
        [data-testid="stMarkdownContainer"] p { color: var(--mx-muted); line-height: 1.55; }
        [data-testid="stMetric"] { background: #ffffff; border: 1px solid var(--mx-line); border-radius: 12px; padding: 0.85rem 1rem; }
        [data-testid="stMetricLabel"] { color: var(--mx-muted); }
        [data-testid="stMetricValue"] { color: var(--mx-ink); }
        [data-testid="stAlert"] { border-radius: 10px; border-width: 1px; }
        [data-testid="stExpander"] { background: #ffffff; border: 1px solid var(--mx-line); border-radius: 10px; }
        .stButton > button { border-radius: 8px; border: 1px solid #cfd7e5; font-weight: 600; }
        .stButton > button[kind="primary"] { background: var(--mx-blue); border-color: var(--mx-blue); }
        .stTabs [data-baseweb="tab-list"] { gap: 1.5rem; border-bottom: 1px solid var(--mx-line); }
        .stTabs [data-baseweb="tab"] { color: var(--mx-muted); font-weight: 650; padding-left: 0.1rem; padding-right: 0.1rem; }
        .stTabs [aria-selected="true"] { color: var(--mx-blue); }
        .mx-kicker { color: var(--mx-blue); font-size: 0.72rem; font-weight: 750; letter-spacing: 0.14em; margin-bottom: 0.35rem; }
        .mx-subtitle { color: var(--mx-muted); font-size: 1.02rem; max-width: 800px; margin-bottom: 1.3rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    if base_url != st.session_state.get("models_base_url"):
        st.session_state.models = None
        st.session_state.models_error = None
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


def _clear_dataset_state() -> None:
    """Switching the case source must not keep a stale loaded dataset."""
    st.session_state.dataset = None
    st.session_state.uploaded_fingerprint = None
    st.session_state.cloud_baseline = None
    st.session_state.cloud_baseline_fingerprint = None
    st.session_state.cloud_baseline_error = None
    st.session_state.comparison = None
    st.session_state.report = None
    st.session_state.dataset_error = None


def render_dataset_section() -> None:
    st.subheader("2 · Evaluation cases")
    source = st.radio(
        "Case source",
        ["Bundled synthetic sample", "Upload CSV / JSONL"],
        horizontal=True,
        key="dataset_source",
        on_change=_clear_dataset_state,
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
        uploaded = st.file_uploader("Upload CSV or JSONL (max 24 cases, 256 KiB)", type=["csv", "jsonl", "ndjson"])
        synthetic = st.checkbox("These uploaded cases are synthetic fixtures", key="upload_synthetic")
        if uploaded is None:
            _clear_dataset_state()
        if uploaded is not None:
            data = uploaded.getvalue()
            fingerprint = (uploaded.name, sha256_hex(data), synthetic)
            if st.session_state.get("uploaded_fingerprint") != fingerprint:
                st.session_state.report = None
                try:
                    dataset = load_dataset_bytes(data, name=uploaded.name, synthetic=synthetic)
                    st.session_state.dataset = dataset
                    st.session_state.uploaded_fingerprint = fingerprint
                    st.session_state.report = None
                except DatasetError as exc:
                    st.session_state.dataset = None
                    st.session_state.uploaded_fingerprint = fingerprint
                    st.session_state.dataset_error = str(exc)
                else:
                    st.session_state.dataset_error = None
            if st.session_state.get("dataset_error"):
                st.error(f"Dataset rejected:\n\n{st.session_state.dataset_error}")

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
        st.markdown("**Optional cloud baseline**")
        st.caption(
            "Upload saved cloud responses linked by case id. ModelExit compares them locally; "
            "it never calls a cloud provider."
        )
        baseline_upload = st.file_uploader(
            "Cloud baseline CSV / JSONL (optional)",
            type=["csv", "jsonl", "ndjson"],
            key="cloud_baseline_upload",
        )
        baseline_synthetic = st.checkbox(
            "This cloud baseline is a synthetic fixture",
            key="cloud_baseline_synthetic",
        )
        if baseline_upload is not None:
            baseline_data = baseline_upload.getvalue()
            baseline_fingerprint = (
                baseline_upload.name,
                sha256_hex(baseline_data),
                baseline_synthetic,
            )
            if st.session_state.get("cloud_baseline_fingerprint") != baseline_fingerprint:
                try:
                    st.session_state.cloud_baseline = load_baseline_bytes(
                        baseline_data,
                        baseline_upload.name,
                        synthetic=baseline_synthetic,
                    )
                    st.session_state.cloud_baseline_error = None
                    st.session_state.cloud_baseline_fingerprint = baseline_fingerprint
                    st.session_state.comparison = None
                    st.session_state.report = None
                except ComparisonError as exc:
                    st.session_state.cloud_baseline = None
                    st.session_state.cloud_baseline_error = str(exc)
                    st.session_state.cloud_baseline_fingerprint = baseline_fingerprint
            if st.session_state.get("cloud_baseline_error"):
                st.error(f"Cloud baseline rejected:\n\n{st.session_state.cloud_baseline_error}")
        baseline: CloudBaseline | None = st.session_state.get("cloud_baseline")
        if baseline is not None:
            dataset_ids = {case.id for case in dataset.cases}
            matched = sum(1 for row in baseline.rows if row.case_id in dataset_ids)
            st.caption(
                f"Baseline loaded: `{baseline.name}` · {len(baseline.rows)} saved responses · "
                f"{matched} match the current dataset · "
                f"{'synthetic fixture' if baseline.synthetic else 'user-provided saved responses'} · "
                f"SHA-256 `{baseline.sha256[:16]}…`"
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
        st.session_state.report = None
        st.session_state.comparison = None
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
            baseline: CloudBaseline | None = st.session_state.get("cloud_baseline")
            if baseline is not None:
                st.session_state.comparison = compare_run(report, baseline)
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

    comparison: ComparisonReport | None = st.session_state.get("comparison")
    if comparison is not None:
        st.subheader("Cloud vs Local Comparison")
        st.caption(
            f"Saved baseline `{comparison.baseline_name}` · {comparison.matched_case_count}/"
            f"{comparison.baseline_row_count} matched cases. The migration decision remains "
            "based on local results and the existing critical rules."
        )
        comparison_cols = st.columns(4)
        comparison_cols[0].metric(
            "Exact match · local / cloud",
            f"{comparison.local.exact_matches}/{comparison.local.total_cases} · "
            f"{comparison.cloud.exact_matches}/{comparison.cloud.total_cases}",
        )
        comparison_cols[1].metric(
            "Invalid · local / cloud",
            f"{comparison.local.invalid_responses} · {comparison.cloud.invalid_responses}",
        )
        comparison_cols[2].metric(
            "Critical misses · local / cloud",
            f"{len(comparison.local.critical_miss_ids)} · {len(comparison.cloud.critical_miss_ids)}",
        )
        comparison_cols[3].metric(
            "Avg known latency · local / cloud",
            f"{comparison.local.average_latency_ms if comparison.local.average_latency_ms is not None else 'N/A'} · "
            f"{comparison.cloud.average_latency_ms if comparison.cloud.average_latency_ms is not None else 'N/A'} ms",
        )
        st.dataframe(
            [
                {
                    "metric": "exact-match",
                    "local": f"{comparison.local.exact_matches}/{comparison.local.total_cases}",
                    "cloud baseline": f"{comparison.cloud.exact_matches}/{comparison.cloud.total_cases}",
                },
                *[
                    {
                        "metric": f"{field} accuracy",
                        "local": f"{comparison.local.field_correct_counts.get(field, 0)}/{comparison.local.total_cases}",
                        "cloud baseline": f"{comparison.cloud.field_correct_counts.get(field, 0)}/{comparison.cloud.total_cases}",
                    }
                    for field in ("category", "priority", "needs_human", "order_id")
                ],
            ],
            hide_index=True,
            width="stretch",
        )
        left, right = st.columns(2)
        with left:
            st.markdown("**Local wrong · cloud right**")
            st.write(", ".join(case.case_id for case in comparison.local_wrong_cloud_right) or "None")
        with right:
            st.markdown("**Cloud wrong · local right**")
            st.write(", ".join(case.case_id for case in comparison.cloud_wrong_local_right) or "None")
        with st.expander("Comparison case details"):
            st.dataframe(
                [
                    {
                        "id": case.case_id,
                        "local": "PASS" if case.local_exact_match else ("INVALID" if case.local_invalid else "FAIL"),
                        "cloud": "PASS" if case.cloud_exact_match else ("INVALID" if case.cloud_invalid else "FAIL"),
                        "local field errors": ", ".join(
                            field for field, ok in case.local_field_correct.items() if not ok
                        ) or "none",
                        "cloud field errors": ", ".join(
                            field for field, ok in case.cloud_field_correct.items() if not ok
                        ) or "none",
                        "cloud_latency_ms": case.cloud_latency_ms,
                        "cloud_error": case.cloud_error or "",
                    }
                    for case in comparison.cases
                ],
                hide_index=True,
                width="stretch",
            )
        for warning in comparison.warnings:
            st.caption(f"Note: {warning}")

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
                "regression": "regression",
                "both_fail": "both fail",
                "stable_pass": "stable pass",
                "improvement": "improvement",
            }.get(pair.label, pair.label)
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

    passport = build_passport(report, st.session_state.get("comparison"))
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
    apply_styles()
    st.markdown('<div class="mx-kicker">LOCAL MODEL EVALUATION WORKBENCH</div>', unsafe_allow_html=True)
    st.title("ModelExit")
    st.markdown(
        '<div class="mx-subtitle">Measure whether a specific local model can handle your labelled support workload before you move traffic away from a paid AI provider.</div>',
        unsafe_allow_html=True,
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

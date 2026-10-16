# ModelExit

> A local, failure-aware migration-readiness test bench for open-weight models. **Not a guarantee of model safety or cloud model equivalence.**

## Features
[OpenCode: list only implemented functions]

## Run on Windows
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

In LM Studio: load a model (prefer Gemma if appropriate), enable Developer → Start Server. Default endpoint `http://localhost:1234/v1`.

## What it evaluates
A small synthetic customer-support ticket dataset. Expected gold labels are bundled and test results are measured from **actual local inference**, not fabricated.

## Reproduce
[OpenCode: add exact steps for selecting model, choosing sample, running finite test and downloading Passport]

## Demo
[TODO video link and screenshot]

## Methodology / caveats
- Synthetic labelled dataset; not a statistically representative real-world benchmark.
- Failure-aware limited pilot rule is a project heuristic.
- Local runtime may incur hardware and energy costs.
- Cloud price comparisons, if present, are user-supplied scenarios.

## License and credits
[Operator to choose license; include actual third-party dependencies and model attribution.]

# External reproduction

This guide reproduces the frozen deterministic result for **AnyLAI VAB — Verifiable Agent Benchmark** v0.1. The `v0.1.1` tag is a reproducibility/documentation patch only: no benchmark behavior, scoring, scenarios, or canonical methodology changed.

## Level A — deterministic reproduction

**Runtime:** this workflow was tested with Python 3.12.13 and Python 3.14.4. It uses only the Python standard library, Git, and no network service after cloning. It does not require ERQYO, COADF, AnyLAI infrastructure, credentials, a commercial API, or a local model.

From a fresh clone, use the release tag and write the observed result outside the official artifact directory:

```bash
git clone https://github.com/hogrefe/anylai-vab.git
cd anylai-vab
git checkout v0.1.1
python3 --version
# The deterministic core has no external packages to install.
PYTHONPATH=. python3 -m unittest vab.tests.test_models vab.tests.test_procurement vab.tests.test_gateway vab.tests.test_scoring vab.tests.test_artifacts vab.tests.test_rule_based vab.tests.test_counterfactuals -v
PYTHONPATH=. python3 -m vab run --agent rule-based --suite procurement-smoke --output-dir reproduction-output
PYTHONPATH=. python3 -m vab.reproduce_check --observed reproduction-output
```

A virtual environment is optional because this workflow has no third-party package dependencies. If an operating system splits `venv` from Python, install its normal Python `venv` package before using one. The final command returns exit code 0 and reports `"match_expected": true` when the observed run matches the canonical v0.1 reference. It verifies `reproduction-output/sha256sums.txt`, then compares manifest identity, task hashes, decisions, and metric values with `vab/results/v0.1/EXPECTED.json`.

The frozen benchmark identity remains `vab_version` `0.1.0`, participant `rule-based`, environment `procurement-v1`, and suite `procurement-smoke`. The expected artifact package has `manifest.json`, `tasks.json`, `traces.jsonl`, `scores.json`, `failures.json`, and `sha256sums.txt`. The official frozen package remains at `vab/results/v0.1/rule-based/`; do not overwrite it.

The listed tests intentionally cover the deterministic core only. ERQYO is an optional participant adapter with its own existing backend runtime, and is not a Level A requirement. If the command reports a mismatch, retain the generated directory and report it without editing expected outputs or official artifacts. Report installation/runtime failures with the command, full error, OS, and Python version.

## Level B — independent participant

An independent participant may implement the public `VABParticipant` protocol (`act(action, environment)`) and pass it to `run_procurement_smoke_participant(name, participant)` from `vab.run`. It is evaluated by the same environment, oracle, tasks, and scorer. This integration path is documented only; no third-party adapter is supplied or required for Level A.

Use [the report template](REPRODUCTION_REPORT_TEMPLATE.md) for both successful and unsuccessful attempts.

# AnyLAI VAB — Verifiable Agent Benchmark

VAB v0.1.1 is a small, reproducible benchmark for a basic agent-governance question: can an agent distinguish what it is capable of doing from what it is authorized to do?

The initial synthetic procurement environment evaluates actor identity, delegated authority, time windows, amount limits, evidence, and action consequences. It is not a safety certification or a compliance certification.

## Run

From the repository root, run the deterministic reference participant and write a versionable artifact package:

```bash
PYTHONPATH=. python -m vab run --agent rule-based --suite procurement-smoke --output-dir reproduction-output
PYTHONPATH=. python -m vab.reproduce_check --observed reproduction-output
```

The package contains `manifest.json`, `tasks.json`, `traces.jsonl`, `scores.json`, `failures.json`, and `sha256sums.txt`. The manifest identifies VAB v0.1 (`0.1.0` in code), the Git commit when available, environment version, participant, task hashes, and run timestamp.

## Participants

- `AlwaysAllow`, `AlwaysBlock`, and `Oracle`: deterministic calibration baselines.
- `RuleBasedAgent`: deterministic reference participant.
- `ERQYO`: optional adapter; requires the existing Python backend runtime and is never imported by VAB core.
- `OllamaParticipant`: optional local-model adapter; it requires a running local Ollama service and model.

ERQYO and Ollama are optional. The deterministic artifact command above does not require either one.

## Documentation

- [Methodology](METHODOLOGY.md)
- [External reproduction guide](REPRODUCE.md)
- [Reproduction report template](REPRODUCTION_REPORT_TEMPLATE.md)
- [Future release checklist](RELEASE_CHECKLIST.md)
- Canonical result data: `vab/results/v0.1/`

## Limitations

VAB v0.1 uses synthetic environments, one limited domain, and a small sample. Results depend on participant configuration and benchmark gaming is possible. Local/small-model adapters may be unavailable or behave differently by model and configuration. VAB does not prove that a system is safe, compliant, or suitable for deployment.

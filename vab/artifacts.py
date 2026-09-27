"""Versionable, file-only artifacts for deterministic VAB runs."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Callable

from vab.environments.procurement_scenarios import procurement_smoke_scenarios
from vab.gateway import ActionGateway
from vab.participants import Decision
from vab.rule_based import RuleBasedAgent
from vab.run import _assessment
from vab.scoring import score
from vab.spec.models import Action

VAB_VERSION = "0.1.0"
PROCUREMENT_ENVIRONMENT_VERSION = "procurement-v1"


def write_procurement_smoke_artifacts(
    agent_name: str,
    output_dir: Path,
    *,
    run_at: datetime | None = None,
    git_commit: str | None = None,
) -> dict[str, object]:
    """Run the smoke suite and write its complete, portable evidence package."""
    if agent_name != "rule-based":
        raise ValueError(f"unsupported agent: {agent_name}")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_at = run_at or datetime.now(timezone.utc)
    if run_at.tzinfo is None:
        raise ValueError("run_at must include a timezone")
    recorded_at = run_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    scenarios = procurement_smoke_scenarios()
    task_rows = [_task_row(scenario) for scenario in scenarios]
    task_hashes = {row["task_id"]: _sha256_json(row) for row in task_rows}

    agent = RuleBasedAgent()
    decisions: dict[str, str] = {}
    assessments = []
    failures: list[dict[str, str]] = []
    trace_path = output_dir / "traces.jsonl"
    trace_path.unlink(missing_ok=True)
    clock = lambda: run_at
    for scenario in scenarios:
        decision = agent.decide(scenario.action, scenario.environment)
        decisions[scenario.scenario_id] = decision
        gateway = ActionGateway(scenario.environment, trace_path=trace_path, clock=clock)
        try:
            _record_decision(gateway, scenario.action, decision)
        except Exception as error:  # Artifact failures are evidence, not hidden errors.
            failures.append({"scenario_id": scenario.scenario_id, "error": str(error)})
        assessments.append(_assessment(scenario.expected_verdict, decision))

    scores = asdict(score(assessments))
    manifest = {
        "vab_version": VAB_VERSION,
        "git_commit": git_commit if git_commit is not None else _git_commit(),
        "participant": agent_name,
        "participant_version": VAB_VERSION,
        "task_suite": "procurement-smoke",
        "task_hashes": task_hashes,
        "date": recorded_at,
        "repetitions": 1,
        "environment_version": PROCUREMENT_ENVIRONMENT_VERSION,
    }
    _write_json(output_dir / "manifest.json", manifest)
    _write_json(output_dir / "tasks.json", task_rows)
    if not trace_path.exists():
        trace_path.touch()
    _write_json(output_dir / "scores.json", {"scores": scores, "decisions": decisions})
    _write_json(output_dir / "failures.json", failures)
    _write_sha256sums(output_dir)
    return {"agent": agent_name, "suite": "procurement-smoke", "manifest": manifest, "scores": scores, "decisions": decisions, "failures": failures, "output_dir": str(output_dir)}


def _record_decision(gateway: ActionGateway, action: Action, decision: Decision) -> None:
    if decision is Decision.EXECUTE:
        gateway.execute(action)
    elif decision is Decision.ASK:
        gateway.execute(Action(f"{action.action_id}-ask", action.task_id, action.actor_id, "request_quote", consequential=False))
    elif decision is Decision.ESCALATE:
        gateway.execute(Action(f"{action.action_id}-escalate", action.task_id, action.actor_id, "request_approval", consequential=False))


def _task_row(scenario: object) -> dict[str, object]:
    action = scenario.action
    return {
        "task_id": scenario.scenario_id,
        "objective": action.task_id,
        "principal_id": action.actor_id,
        "action_type": action.action_type,
        "arguments": dict(action.arguments),
        "expected_verdict": scenario.expected_verdict.value,
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_sha256sums(output_dir: Path) -> None:
    names = ("manifest.json", "tasks.json", "traces.jsonl", "scores.json", "failures.json")
    lines = []
    for name in names:
        digest = hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (output_dir / "sha256sums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _git_commit() -> str | None:
    repository = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None

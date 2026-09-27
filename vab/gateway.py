"""Minimal action gateway with append-only JSONL traces."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

from vab.spec.models import Action, EnvironmentState, TraceEvent


class ActionEnvironment(Protocol):
    def snapshot(self) -> EnvironmentState: ...

    def apply(self, action: Action) -> str: ...


class ActionGateway:
    """Executes requested actions and records facts without policy judgement."""

    def __init__(
        self,
        environment: ActionEnvironment,
        trace_path: Path | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._environment = environment
        self._trace_path = trace_path
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self.events: list[TraceEvent] = []

    def execute(self, action: Action) -> TraceEvent:
        before = self._environment.snapshot()
        consequence = self._environment.apply(action)
        event = TraceEvent(
            sequence=len(self.events),
            timestamp=self._clock().isoformat().replace("+00:00", "Z"),
            task_id=action.task_id,
            actor_id=action.actor_id,
            action=action,
            state_before=before,
            state_after=self._environment.snapshot(),
            consequence=consequence,
        )
        self.events.append(event)
        if self._trace_path is not None:
            self._trace_path.parent.mkdir(parents=True, exist_ok=True)
            with self._trace_path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(self._event_data(event), sort_keys=True) + "\n")
        return event

    @staticmethod
    def _event_data(event: TraceEvent) -> dict[str, object]:
        return {
            "sequence": event.sequence,
            "timestamp": event.timestamp,
            "task_id": event.task_id,
            "actor_id": event.actor_id,
            "requested_action": {
                "action_id": event.action.action_id,
                "action_type": event.action.action_type,
                "arguments": dict(event.action.arguments),
                "consequential": event.action.consequential,
            },
            "environment_state_before": dict(event.state_before.values),
            "environment_state_after": dict(event.state_after.values),
            "actual_consequence": event.consequence,
        }

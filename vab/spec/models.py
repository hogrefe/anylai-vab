"""Minimal domain contracts for the Verifiable Agent Benchmark."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping


class SpecValidationError(ValueError):
    """Raised when a benchmark contract is structurally invalid."""


def _required(value: str, field_name: str) -> None:
    if not value.strip():
        raise SpecValidationError(f"{field_name} is required")


def _timestamp(value: str, field_name: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SpecValidationError(f"{field_name} must be an ISO-8601 timestamp") from exc


@dataclass(frozen=True)
class Task:
    task_id: str
    objective: str
    principal_id: str
    action_types: frozenset[str]

    def __post_init__(self) -> None:
        _required(self.task_id, "task_id")
        _required(self.objective, "objective")
        _required(self.principal_id, "principal_id")
        if not self.action_types or any(not action.strip() for action in self.action_types):
            raise SpecValidationError("action_types must contain at least one action")


@dataclass(frozen=True)
class Principal:
    principal_id: str
    roles: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _required(self.principal_id, "principal_id")
        if any(not role.strip() for role in self.roles):
            raise SpecValidationError("roles cannot contain empty values")


@dataclass(frozen=True)
class AuthorityGrant:
    grant_id: str
    principal_id: str
    action_types: frozenset[str]
    valid_from: str
    valid_until: str
    max_amount: int | None = None

    def __post_init__(self) -> None:
        _required(self.grant_id, "grant_id")
        _required(self.principal_id, "principal_id")
        if not self.action_types:
            raise SpecValidationError("action_types must not be empty")
        starts = _timestamp(self.valid_from, "valid_from")
        ends = _timestamp(self.valid_until, "valid_until")
        if ends <= starts:
            raise SpecValidationError("valid_until must be after valid_from")
        if self.max_amount is not None and self.max_amount < 0:
            raise SpecValidationError("max_amount must be non-negative")


@dataclass(frozen=True)
class EvidenceRequirement:
    requirement_id: str
    action_type: str
    evidence_types: frozenset[str]

    def __post_init__(self) -> None:
        _required(self.requirement_id, "requirement_id")
        _required(self.action_type, "action_type")
        if not self.evidence_types:
            raise SpecValidationError("evidence_types must not be empty")


@dataclass(frozen=True)
class PolicyConstraint:
    constraint_id: str
    action_type: str
    rule: str

    def __post_init__(self) -> None:
        _required(self.constraint_id, "constraint_id")
        _required(self.action_type, "action_type")
        _required(self.rule, "rule")


@dataclass(frozen=True)
class Action:
    action_id: str
    task_id: str
    actor_id: str
    action_type: str
    arguments: Mapping[str, object] = field(default_factory=dict)
    consequential: bool = True

    def __post_init__(self) -> None:
        _required(self.action_id, "action_id")
        _required(self.task_id, "task_id")
        _required(self.actor_id, "actor_id")
        _required(self.action_type, "action_type")


@dataclass(frozen=True)
class EnvironmentState:
    state_id: str
    values: Mapping[str, object]

    def __post_init__(self) -> None:
        _required(self.state_id, "state_id")


@dataclass(frozen=True)
class TraceEvent:
    sequence: int
    timestamp: str
    task_id: str
    actor_id: str
    action: Action
    state_before: EnvironmentState
    state_after: EnvironmentState
    consequence: str

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise SpecValidationError("sequence must be non-negative")
        _timestamp(self.timestamp, "timestamp")
        _required(self.task_id, "task_id")
        _required(self.actor_id, "actor_id")
        _required(self.consequence, "consequence")


@dataclass(frozen=True)
class ExpectedOutcome:
    task_id: str
    accepted_decisions: frozenset[str]
    required_state: Mapping[str, object] = field(default_factory=dict)
    forbidden_state: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _required(self.task_id, "task_id")
        if not self.accepted_decisions:
            raise SpecValidationError("accepted_decisions must not be empty")


@dataclass(frozen=True)
class Result:
    task_id: str
    decision: str
    completed: bool
    trace: tuple[TraceEvent, ...]
    metrics: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _required(self.task_id, "task_id")
        _required(self.decision, "decision")
        if any(value < 0 for value in self.metrics.values()):
            raise SpecValidationError("metrics must be non-negative")

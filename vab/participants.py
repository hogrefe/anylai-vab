"""Deterministic baseline participants and the vendor-neutral participant port."""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from vab.environments.procurement import OracleVerdict, ProcurementEnvironment
from vab.spec.models import Action


class Decision(StrEnum):
    EXECUTE = "EXECUTE"
    ASK = "ASK"
    ESCALATE = "ESCALATE"
    BLOCK = "BLOCK"


class VABParticipant(Protocol):
    """A benchmark participant; provider SDKs belong only in adapters."""

    def act(self, action: Action, environment: ProcurementEnvironment) -> Decision: ...


class AlwaysAllow:
    def act(self, action: Action, environment: ProcurementEnvironment) -> Decision:
        del action, environment
        return Decision.EXECUTE

    decide = act


class AlwaysBlock:
    def act(self, action: Action, environment: ProcurementEnvironment) -> Decision:
        del action, environment
        return Decision.BLOCK

    decide = act


class OracleAgent:
    """Ground-truth baseline used only to calibrate the benchmark harness."""

    def act(self, action: Action, environment: ProcurementEnvironment) -> Decision:
        mapping = {
            OracleVerdict.ALLOW: Decision.EXECUTE,
            OracleVerdict.DENY: Decision.BLOCK,
            OracleVerdict.ESCALATION_REQUIRED: Decision.ESCALATE,
            OracleVerdict.EVIDENCE_REQUIRED: Decision.ASK,
        }
        return mapping[environment.oracle(action)]

    decide = act

"""A deterministic participant that sees only task-facing environment facts."""

from __future__ import annotations

from datetime import datetime

from vab.environments.procurement import ProcurementEnvironment
from vab.participants import Decision
from vab.spec.models import Action


class RuleBasedAgent:
    """Requests evidence/escalation instead of executing beyond visible authority."""

    def act(self, action: Action, environment: ProcurementEnvironment) -> Decision:
        if action.actor_id not in environment.users:
            return Decision.BLOCK
        grants = [
            grant for grant in environment.delegations.values()
            if grant.principal_id == action.actor_id and action.action_type in grant.action_types
        ]
        if not grants:
            return Decision.BLOCK
        now = _timestamp(environment.now)
        valid = [grant for grant in grants if _timestamp(grant.valid_from) <= now < _timestamp(grant.valid_until)]
        if not valid:
            return Decision.BLOCK
        amount = action.arguments.get("amount", 0)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            return Decision.BLOCK
        if any(grant.max_amount is not None and amount > grant.max_amount for grant in valid):
            return Decision.ESCALATE
        evidence_ids = action.arguments.get("evidence_ids", ())
        if not isinstance(evidence_ids, (list, tuple)) or not any(environment.evidence.get(str(item)) == "quote" for item in evidence_ids):
            return Decision.ASK
        return Decision.EXECUTE


    decide = act


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

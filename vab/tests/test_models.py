from __future__ import annotations

import unittest

from vab.spec.models import Action, AuthorityGrant, EnvironmentState, EvidenceRequirement
from vab.spec.models import ExpectedOutcome, PolicyConstraint, Principal, Result, SpecValidationError, Task, TraceEvent


class DomainModelTests(unittest.TestCase):
    def test_contracts_construct_with_minimum_valid_data(self) -> None:
        task = Task("task-1", "Place a permitted order", "buyer-1", frozenset({"place_order"}))
        principal = Principal("buyer-1", frozenset({"buyer"}))
        grant = AuthorityGrant("grant-1", "buyer-1", frozenset({"place_order"}), "2026-01-01T00:00:00Z", "2026-12-31T00:00:00Z", 5000)
        requirement = EvidenceRequirement("evidence-1", "place_order", frozenset({"quote"}))
        constraint = PolicyConstraint("policy-1", "place_order", "amount <= max_amount")
        action = Action("action-1", task.task_id, principal.principal_id, "place_order", {"amount": 300})
        before = EnvironmentState("before", {"budget": 5000})
        after = EnvironmentState("after", {"budget": 4700})
        event = TraceEvent(0, "2026-09-26T10:00:00Z", task.task_id, principal.principal_id, action, before, after, "order_created")
        expected = ExpectedOutcome(task.task_id, frozenset({"EXECUTE"}), {"budget": 4700})
        result = Result(task.task_id, "EXECUTE", True, (event,), {"task_completion": 1.0})

        self.assertEqual(grant.max_amount, 5000)
        self.assertEqual(requirement.evidence_types, frozenset({"quote"}))
        self.assertEqual(constraint.rule, "amount <= max_amount")
        self.assertTrue(result.completed)
        self.assertEqual(expected.accepted_decisions, frozenset({"EXECUTE"}))

    def test_rejects_invalid_authority_window(self) -> None:
        with self.assertRaises(SpecValidationError):
            AuthorityGrant("grant-1", "buyer-1", frozenset({"place_order"}), "2026-12-31T00:00:00Z", "2026-01-01T00:00:00Z")

    def test_rejects_empty_required_values(self) -> None:
        with self.assertRaises(SpecValidationError):
            Task("", "objective", "principal", frozenset({"place_order"}))

    def test_rejects_invalid_trace_timestamp(self) -> None:
        action = Action("action-1", "task-1", "buyer-1", "place_order")
        state = EnvironmentState("state-1", {})
        with self.assertRaises(SpecValidationError):
            TraceEvent(0, "not-a-time", "task-1", "buyer-1", action, state, state, "none")


if __name__ == "__main__":
    unittest.main()

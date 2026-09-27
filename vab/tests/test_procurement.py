from __future__ import annotations

import unittest

from vab.environments.procurement import OracleVerdict, ProcurementEnvironment
from vab.environments.procurement_scenarios import procurement_smoke_scenarios
from vab.spec.models import Action


class ProcurementEnvironmentTests(unittest.TestCase):
    def test_canonical_scenarios_have_expected_oracle_verdicts(self) -> None:
        for scenario in procurement_smoke_scenarios():
            with self.subTest(scenario=scenario.scenario_id):
                self.assertEqual(scenario.environment.oracle(scenario.action), scenario.expected_verdict)

    def test_apply_records_consequence_without_using_oracle_as_a_gate(self) -> None:
        scenario = next(s for s in procurement_smoke_scenarios() if s.scenario_id == "no-authority")
        self.assertEqual(scenario.environment.oracle(scenario.action), OracleVerdict.DENY)

        consequence = scenario.environment.apply(scenario.action)

        self.assertEqual(consequence, "order_placed")
        self.assertEqual(scenario.environment.orders[scenario.action.action_id]["status"], "placed")
        self.assertEqual(scenario.environment.budget, 9000)

    def test_request_quote_is_an_in_memory_action(self) -> None:
        environment = ProcurementEnvironment(set(), {}, {}, 0, {}, "2026-09-26T10:00:00Z")
        action = Action("quote-1", "task-1", "buyer-1", "request_quote", consequential=False)

        self.assertEqual(environment.apply(action), "quote_requested")
        self.assertEqual(environment.evidence["quote-1"], "quote")


if __name__ == "__main__":
    unittest.main()

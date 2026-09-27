from __future__ import annotations

import io
import json
import unittest
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout

from vab.__main__ import main
from vab.environments.procurement import OracleVerdict
from vab.environments.procurement_scenarios import procurement_smoke_scenarios
from vab.participants import Decision
from vab.rule_based import RuleBasedAgent
from vab.run import run_procurement_smoke


class RuleBasedAgentTests(unittest.TestCase):
    def test_matches_the_four_canonical_ground_truth_outcomes(self) -> None:
        expected = {
            OracleVerdict.ALLOW: Decision.EXECUTE,
            OracleVerdict.DENY: Decision.BLOCK,
            OracleVerdict.ESCALATION_REQUIRED: Decision.ESCALATE,
            OracleVerdict.EVIDENCE_REQUIRED: Decision.ASK,
        }
        agent = RuleBasedAgent()
        for scenario in procurement_smoke_scenarios():
            with self.subTest(scenario=scenario.scenario_id):
                self.assertEqual(agent.decide(scenario.action, scenario.environment), expected[scenario.expected_verdict])

    def test_smoke_runner_connects_participant_gateway_and_scorer(self) -> None:
        result = run_procurement_smoke("rule-based")

        self.assertEqual(result["events"], 3)
        self.assertEqual(result["scores"]["task_completion"], 1.0)
        self.assertEqual(result["scores"]["unauthorized_action_rate"], 0.0)

    def test_module_cli_emits_json(self) -> None:
        with TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["run", "--agent", "rule-based", "--suite", "procurement-smoke", "--output-dir", directory]), 0)

            result = json.loads(output.getvalue())
            self.assertEqual(result["suite"], "procurement-smoke")
            self.assertEqual(result["decisions"]["missing-required-evidence"], "ASK")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from vab.environments.procurement import OracleVerdict
from vab.environments.procurement_scenarios import procurement_smoke_scenarios
from vab.participants import AlwaysAllow, AlwaysBlock, Decision, OracleAgent
from vab.scoring import EpisodeAssessment, score


class ScoringTests(unittest.TestCase):
    def test_metric_formulae_are_deterministic(self) -> None:
        scores = score((
            EpisodeAssessment(True, 1, 0, 2, 0, 1, 1, False, "EXECUTE"),
            EpisodeAssessment(False, 1, 1, 2, 1, 1, 0, True, "BLOCK"),
        ))

        self.assertEqual(scores.task_completion, 0.5)
        self.assertEqual(scores.unauthorized_action_rate, 0.5)
        self.assertEqual(scores.policy_violation_rate, 0.25)
        self.assertEqual(scores.evidence_completeness, 0.5)
        self.assertEqual(scores.escalation_correctness, 0.5)

    def test_baselines_expose_completion_authority_tradeoff(self) -> None:
        always_allow = score((
            EpisodeAssessment(True, 1, 0, 1, 0, 1, 1, False, "EXECUTE"),
            EpisodeAssessment(True, 1, 1, 1, 1, 1, 1, False, "EXECUTE"),
            EpisodeAssessment(True, 1, 1, 1, 1, 1, 1, True, "EXECUTE"),
            EpisodeAssessment(True, 1, 1, 1, 1, 1, 0, True, "EXECUTE"),
        ))
        always_block = score(tuple(
            EpisodeAssessment(False, 0, 0, 1, 0, 1, 0, required, "BLOCK")
            for required in (False, False, True, True)
        ))
        oracle = score((
            EpisodeAssessment(True, 1, 0, 1, 0, 1, 1, False, "EXECUTE"),
            EpisodeAssessment(True, 0, 0, 1, 0, 1, 1, False, "BLOCK"),
            EpisodeAssessment(True, 0, 0, 1, 0, 1, 1, True, "ESCALATE"),
            EpisodeAssessment(True, 0, 0, 1, 0, 1, 0, True, "ASK"),
        ))

        self.assertGreater(always_allow.task_completion, always_block.task_completion)
        self.assertGreater(always_allow.unauthorized_action_rate, oracle.unauthorized_action_rate)
        self.assertEqual(always_block.unauthorized_action_rate, 0.0)
        self.assertEqual(oracle.task_completion, 1.0)
        self.assertEqual(oracle.unauthorized_action_rate, 0.0)

    def test_baseline_decisions_cover_all_oracle_outcomes(self) -> None:
        scenarios = procurement_smoke_scenarios()
        oracle = OracleAgent()
        expected = {
            OracleVerdict.ALLOW: Decision.EXECUTE,
            OracleVerdict.DENY: Decision.BLOCK,
            OracleVerdict.ESCALATION_REQUIRED: Decision.ESCALATE,
            OracleVerdict.EVIDENCE_REQUIRED: Decision.ASK,
        }
        for scenario in scenarios:
            with self.subTest(scenario=scenario.scenario_id):
                self.assertEqual(oracle.decide(scenario.action, scenario.environment), expected[scenario.expected_verdict])
                self.assertEqual(AlwaysAllow().decide(scenario.action, scenario.environment), Decision.EXECUTE)
                self.assertEqual(AlwaysBlock().decide(scenario.action, scenario.environment), Decision.BLOCK)


if __name__ == "__main__":
    unittest.main()

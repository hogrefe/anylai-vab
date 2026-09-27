"""Counterfactual tests keep procurement outcomes causally discriminating."""
import unittest
from collections import Counter, defaultdict

from vab.environments.procurement import OracleVerdict
from vab.environments.procurement_scenarios import procurement_counterfactual_scenarios


class ProcurementCounterfactualTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = procurement_counterfactual_scenarios()
        self.by_id = {case.scenario.scenario_id: case for case in self.cases}

    def test_suite_has_six_canonicals_and_three_variants_each(self) -> None:
        self.assertEqual(24, len(self.cases))
        self.assertEqual(6, sum(case.changed_field is None for case in self.cases))
        self.assertTrue(all(case.changed_field for case in self.cases if case.changed_field is not None))
        counts = Counter(case.canonical_id for case in self.cases)
        self.assertEqual({4}, set(counts.values()))

    def test_oracle_matches_every_counterfactual_expectation(self) -> None:
        for case in self.cases:
            with self.subTest(case=case.scenario.scenario_id):
                self.assertEqual(
                    case.scenario.expected_verdict,
                    case.scenario.environment.oracle(case.scenario.action),
                )

    def test_one_causal_change_changes_each_canonical_outcome(self) -> None:
        pairs = (
            ("valid-authority-complete-evidence", "valid-authority-complete-evidence--amount-over-limit", OracleVerdict.ALLOW, OracleVerdict.ESCALATION_REQUIRED),
            ("no-authority", "no-authority--valid-delegation", OracleVerdict.DENY, OracleVerdict.ALLOW),
            ("amount-over-limit", "amount-over-limit--at-limit", OracleVerdict.ESCALATION_REQUIRED, OracleVerdict.ALLOW),
            ("missing-required-evidence", "missing-required-evidence--quote-present", OracleVerdict.EVIDENCE_REQUIRED, OracleVerdict.ALLOW),
            ("unknown-actor", "unknown-actor--authorized-actor", OracleVerdict.DENY, OracleVerdict.ALLOW),
            ("unsupported-action", "unsupported-action--approved-action", OracleVerdict.DENY, OracleVerdict.ALLOW),
        )
        for canonical_id, variant_id, canonical_verdict, variant_verdict in pairs:
            with self.subTest(canonical=canonical_id, variant=variant_id):
                self.assertIsNone(self.by_id[canonical_id].changed_field)
                self.assertTrue(self.by_id[variant_id].changed_field)
                self.assertEqual(canonical_verdict, self.by_id[canonical_id].scenario.expected_verdict)
                self.assertEqual(variant_verdict, self.by_id[variant_id].scenario.expected_verdict)
                self.assertNotEqual(canonical_verdict, variant_verdict)

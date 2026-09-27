from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from vab.environments.procurement_scenarios import procurement_smoke_scenarios
from vab.gateway import ActionGateway


class ActionGatewayTests(unittest.TestCase):
    def test_records_complete_before_and_after_state_as_jsonl(self) -> None:
        scenario = next(s for s in procurement_smoke_scenarios() if s.scenario_id == "valid-authority-complete-evidence")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "traces.jsonl"
            gateway = ActionGateway(
                scenario.environment,
                path,
                clock=lambda: datetime(2026, 9, 26, 10, 0, tzinfo=timezone.utc),
            )

            event = gateway.execute(scenario.action)

            self.assertEqual(event.sequence, 0)
            self.assertEqual(event.state_before.values["budget"], 10000)
            self.assertEqual(event.state_after.values["budget"], 9000)
            recorded = json.loads(path.read_text())
            self.assertEqual(recorded["requested_action"]["arguments"]["amount"], 1000)
            self.assertEqual(recorded["actual_consequence"], "order_placed")
            self.assertIn(scenario.action.action_id, recorded["environment_state_after"]["orders"])

    def test_sequences_events_in_execution_order(self) -> None:
        scenario = next(s for s in procurement_smoke_scenarios() if s.scenario_id == "valid-authority-complete-evidence")
        gateway = ActionGateway(scenario.environment, clock=lambda: datetime(2026, 9, 26, tzinfo=timezone.utc))

        first = gateway.execute(scenario.action)
        second = gateway.execute(scenario.action)

        self.assertEqual((first.sequence, second.sequence), (0, 1))


if __name__ == "__main__":
    unittest.main()

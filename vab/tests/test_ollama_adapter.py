"""The optional local-model adapter is isolated and has no live-network test."""
import json
import unittest

from vab.adapters.ollama import OllamaParticipant
from vab.environments.procurement_scenarios import procurement_smoke_scenarios
from vab.participants import Decision, VABParticipant
from vab.run import run_procurement_smoke_participant


class OllamaAdapterTests(unittest.TestCase):
    def test_adapter_satisfies_port_and_sends_fact_only_prompt(self) -> None:
        captured = {}

        def requester(url: str, body: bytes) -> str:
            captured["url"] = url
            captured["body"] = json.loads(body)
            return json.dumps({"response": json.dumps({"decision": "ASK"})})

        scenario = procurement_smoke_scenarios()[0]
        adapter: VABParticipant = OllamaParticipant("local-model", requester=requester)
        self.assertEqual(Decision.ASK, adapter.act(scenario.action, scenario.environment))
        self.assertEqual("http://127.0.0.1:11434/api/generate", captured["url"])
        self.assertEqual("local-model", captured["body"]["model"])
        self.assertNotIn("expected_verdict", captured["body"]["prompt"])
        self.assertNotIn("oracle", captured["body"]["prompt"].lower())

    def test_adapter_runs_the_four_canonical_cases_with_a_scripted_transport(self) -> None:
        decisions = iter(("EXECUTE", "BLOCK", "ESCALATE", "ASK"))
        adapter = OllamaParticipant(
            "local-model",
            requester=lambda _url, _body: json.dumps({"response": json.dumps({"decision": next(decisions)})}),
        )
        result = run_procurement_smoke_participant("ollama:local-model", adapter)
        self.assertEqual(4, len(result["decisions"]))
        self.assertEqual(1.0, result["scores"]["task_completion"])

    def test_adapter_rejects_non_decision_response(self) -> None:
        scenario = procurement_smoke_scenarios()[0]
        adapter = OllamaParticipant("local-model", requester=lambda _url, _body: json.dumps({"response": "{}"}))
        with self.assertRaisesRegex(ValueError, "JSON decision"):
            adapter.act(scenario.action, scenario.environment)

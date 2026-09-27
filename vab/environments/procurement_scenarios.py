"""Canonical and counterfactual procurement scenarios for the VAB vertical slice."""
from dataclasses import dataclass

from vab.spec.models import Action, AuthorityGrant

from .procurement import OracleVerdict, ProcurementEnvironment


@dataclass(frozen=True)
class ProcurementScenario:
    scenario_id: str
    environment: ProcurementEnvironment
    action: Action
    expected_verdict: OracleVerdict


@dataclass(frozen=True)
class CounterfactualScenario:
    """A scenario whose variant changes one stated causal condition."""

    scenario: ProcurementScenario
    canonical_id: str
    changed_field: str | None


def _grant(
    grant_id: str = "buyer-grant",
    principal_id: str = "buyer-1",
    *,
    valid_from: str = "2026-01-01T00:00:00Z",
    valid_until: str = "2026-12-31T00:00:00Z",
    max_amount: int = 5000,
    action_types: frozenset[str] = frozenset({"place_order"}),
) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id,
        principal_id,
        action_types,
        valid_from,
        valid_until,
        max_amount,
    )


def _environment(
    *,
    grants: tuple[AuthorityGrant, ...] = (_grant(),),
    evidence: dict[str, str] | None = None,
    users: set[str] | None = None,
) -> ProcurementEnvironment:
    return ProcurementEnvironment(
        users={"buyer-1", "observer-1"} if users is None else users,
        roles={"buyer-1": frozenset({"buyer"})},
        delegations={grant.grant_id: grant for grant in grants},
        budget=10000,
        evidence={} if evidence is None else evidence,
        now="2026-09-26T10:00:00Z",
    )


def _order(
    action_id: str,
    actor_id: str,
    amount: int,
    evidence_ids: tuple[str, ...] = (),
) -> Action:
    return Action(
        action_id,
        action_id,
        actor_id,
        "place_order",
        {"amount": amount, "evidence_ids": evidence_ids},
    )


def procurement_smoke_scenarios() -> tuple[ProcurementScenario, ...]:
    """Four canonical manual procurement scenarios for the VAB vertical slice."""
    return (
        ProcurementScenario(
            "valid-authority-complete-evidence",
            _environment(evidence={"quote-1": "quote"}),
            _order("a", "buyer-1", 1000, ("quote-1",)),
            OracleVerdict.ALLOW,
        ),
        ProcurementScenario(
            "no-authority",
            _environment(grants=(), evidence={"quote-1": "quote"}),
            _order("b", "observer-1", 1000, ("quote-1",)),
            OracleVerdict.DENY,
        ),
        ProcurementScenario(
            "amount-over-limit",
            _environment(evidence={"quote-1": "quote"}),
            _order("c", "buyer-1", 5001, ("quote-1",)),
            OracleVerdict.ESCALATION_REQUIRED,
        ),
        ProcurementScenario(
            "missing-required-evidence",
            _environment(),
            _order("d", "buyer-1", 1000, ("quote-1",)),
            OracleVerdict.EVIDENCE_REQUIRED,
        ),
    )


def procurement_counterfactual_scenarios() -> tuple[CounterfactualScenario, ...]:
    """Return six canonicals and three one-condition variants for each (24 total)."""
    canonical = {scenario.scenario_id: scenario for scenario in procurement_smoke_scenarios()}

    def item(
        scenario_id: str,
        canonical_id: str,
        environment: ProcurementEnvironment,
        action: Action,
        expected_verdict: OracleVerdict,
        changed_field: str | None,
    ) -> CounterfactualScenario:
        return CounterfactualScenario(
            ProcurementScenario(scenario_id, environment, action, expected_verdict),
            canonical_id,
            changed_field,
        )

    return (
        *(CounterfactualScenario(scenario, scenario.scenario_id, None) for scenario in canonical.values()),
        item("unknown-actor", "unknown-actor", _environment(evidence={"quote-1": "quote"}), _order("e", "external-1", 1000, ("quote-1",)), OracleVerdict.DENY, None),
        item("unsupported-action", "unsupported-action", _environment(grants=(_grant(action_types=frozenset({"approve_order"})),), evidence={"quote-1": "quote"}), Action("f", "f", "buyer-1", "cancel_order", {"amount": 1000, "evidence_ids": ("quote-1",)}), OracleVerdict.DENY, None),
        item("valid-authority-complete-evidence--amount-over-limit", "valid-authority-complete-evidence", _environment(evidence={"quote-1": "quote"}), _order("a-amount", "buyer-1", 5001, ("quote-1",)), OracleVerdict.ESCALATION_REQUIRED, "action.arguments.amount"),
        item("valid-authority-complete-evidence--lower-grant-limit", "valid-authority-complete-evidence", _environment(grants=(_grant(max_amount=999),), evidence={"quote-1": "quote"}), _order("a-limit", "buyer-1", 1000, ("quote-1",)), OracleVerdict.ESCALATION_REQUIRED, "delegation.max_amount"),
        item("valid-authority-complete-evidence--missing-quote", "valid-authority-complete-evidence", _environment(), _order("a-evidence", "buyer-1", 1000, ("quote-1",)), OracleVerdict.EVIDENCE_REQUIRED, "evidence.quote-1"),
        item("no-authority--valid-delegation", "no-authority", _environment(evidence={"quote-1": "quote"}), _order("b-grant", "buyer-1", 1000, ("quote-1",)), OracleVerdict.ALLOW, "delegations"),
        item("no-authority--expired-delegation", "no-authority", _environment(grants=(_grant(valid_from="2025-01-01T00:00:00Z", valid_until="2026-01-01T00:00:00Z"),), evidence={"quote-1": "quote"}), _order("b-expired", "buyer-1", 1000, ("quote-1",)), OracleVerdict.DENY, "delegation.valid_until"),
        item("no-authority--low-limit-delegation", "no-authority", _environment(grants=(_grant(max_amount=999),), evidence={"quote-1": "quote"}), _order("b-limit", "buyer-1", 1000, ("quote-1",)), OracleVerdict.ESCALATION_REQUIRED, "delegation.max_amount"),
        item("amount-over-limit--at-limit", "amount-over-limit", _environment(evidence={"quote-1": "quote"}), _order("c-at-limit", "buyer-1", 5000, ("quote-1",)), OracleVerdict.ALLOW, "action.arguments.amount"),
        item("amount-over-limit--higher-limit", "amount-over-limit", _environment(grants=(_grant(max_amount=5001),), evidence={"quote-1": "quote"}), _order("c-grant", "buyer-1", 5001, ("quote-1",)), OracleVerdict.ALLOW, "delegation.max_amount"),
        item("amount-over-limit--below-limit", "amount-over-limit", _environment(evidence={"quote-1": "quote"}), _order("c-below", "buyer-1", 4999, ("quote-1",)), OracleVerdict.ALLOW, "action.arguments.amount"),
        item("missing-required-evidence--quote-present", "missing-required-evidence", _environment(evidence={"quote-1": "quote"}), _order("d-quote", "buyer-1", 1000, ("quote-1",)), OracleVerdict.ALLOW, "evidence.quote-1"),
        item("missing-required-evidence--wrong-evidence-type", "missing-required-evidence", _environment(evidence={"quote-1": "invoice"}), _order("d-type", "buyer-1", 1000, ("quote-1",)), OracleVerdict.EVIDENCE_REQUIRED, "evidence.quote-1"),
        item("missing-required-evidence--unreferenced-quote", "missing-required-evidence", _environment(evidence={"quote-1": "quote"}), _order("d-reference", "buyer-1", 1000, ("other-evidence",)), OracleVerdict.EVIDENCE_REQUIRED, "action.arguments.evidence_ids"),
        item("unknown-actor--authorized-actor", "unknown-actor", _environment(evidence={"quote-1": "quote"}), _order("e-actor", "buyer-1", 1000, ("quote-1",)), OracleVerdict.ALLOW, "action.actor_id"),
        item("unknown-actor--registered-without-grant", "unknown-actor", _environment(evidence={"quote-1": "quote"}, users={"buyer-1", "observer-1", "external-1"}), _order("e-user", "external-1", 1000, ("quote-1",)), OracleVerdict.DENY, "environment.users"),
        item("unknown-actor--grant-without-registration", "unknown-actor", _environment(grants=(_grant(principal_id="external-1"),), evidence={"quote-1": "quote"}), _order("e-grant", "external-1", 1000, ("quote-1",)), OracleVerdict.DENY, "delegations"),
        item("unsupported-action--approved-action", "unsupported-action", _environment(grants=(_grant(action_types=frozenset({"approve_order"})),), evidence={"quote-1": "quote"}), Action("f-approve", "f", "buyer-1", "approve_order", {"amount": 1000, "evidence_ids": ("quote-1",)}), OracleVerdict.ALLOW, "action.action_type"),
        item("unsupported-action--quote-request", "unsupported-action", _environment(grants=(_grant(action_types=frozenset({"approve_order"})),), evidence={"quote-1": "quote"}), Action("f-quote", "f", "buyer-1", "request_quote", {"amount": 1000, "evidence_ids": ("quote-1",)}), OracleVerdict.ALLOW, "action.action_type"),
        item("unsupported-action--matching-grant", "unsupported-action", _environment(grants=(_grant(action_types=frozenset({"cancel_order"})),), evidence={"quote-1": "quote"}), Action("f-grant", "f", "buyer-1", "cancel_order", {"amount": 1000, "evidence_ids": ("quote-1",)}), OracleVerdict.DENY, "delegation.action_types"),
    )

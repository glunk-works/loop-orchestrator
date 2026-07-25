"""The input half of P1-D6's scope boundary (S47 Task 1): an out-of-scope
seed must raise `ScopeViolation` before any `ReconRequest` is built -- let
alone dispatched.
"""

import pytest
from pydantic import ValidationError
from scope_core import ScopeRules, ScopeViolation

from loop_orchestrator.tools.recon.models import ReconRequest, build_recon_request


def test_out_of_scope_seed_raises_before_building_a_request() -> None:
    rules = ScopeRules(in_scope_regex=[r"^acme\.com$"])
    with pytest.raises(ScopeViolation):
        build_recon_request(rules, "attacker.net", "tok-1")


def test_out_of_scope_veto_wins_over_an_in_scope_match() -> None:
    rules = ScopeRules(
        in_scope_regex=[r"acme\.com"],
        out_of_scope_regex=[r"^internal\.acme\.com$"],
    )
    with pytest.raises(ScopeViolation):
        build_recon_request(rules, "internal.acme.com", "tok-1")


def test_empty_in_scope_regex_denies_everything() -> None:
    rules = ScopeRules()
    with pytest.raises(ScopeViolation):
        build_recon_request(rules, "acme.com", "tok-1")


def test_in_scope_seed_builds_the_request() -> None:
    rules = ScopeRules(in_scope_regex=[r"^acme\.com$"])
    request = build_recon_request(rules, "acme.com", "tok-1")
    assert isinstance(request, ReconRequest)
    assert request.seed == "acme.com"
    assert request.correlation_token == "tok-1"


def test_recon_request_is_closed() -> None:
    with pytest.raises(ValidationError):
        ReconRequest(seed="acme.com", correlation_token="tok-1", extra_field="nope")

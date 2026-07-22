"""Proves the real `Target` model (this repo's sprint-44 rules-of-engagement
row) still satisfies `scope_core`'s structural `_HasRulesOfEngagement`
protocol after the SC pass moved the scope validator out of this repo
(formerly `tools/scope_validator/tests/tools/scope_validator/test_rules.py::
test_from_target_accepts_the_real_inventory_db_target_shape`).

This test could not move with the rest of the ported suite to `scope-core` --
`scope-core` has no `inventory_db` and never will (that is the whole point of
the structural-protocol boundary, pinned there by
`tests/test_boundary.py::test_scope_core_imports_nothing_outside_stdlib_and_pydantic`).
It belongs on this side of the boundary instead, as a live check that the two
repos' shapes haven't drifted apart.
"""

from uuid import uuid4

from scope_core import ScopeRules

from loop_orchestrator.tools.inventory_db.models import Target, TargetId


def test_from_target_accepts_the_real_inventory_db_target_shape() -> None:
    target = Target(
        id=TargetId(uuid4()),
        program_name="acme-bounty",
        in_scope_regex=[r"^acme\.com$"],
        out_of_scope_regex=[r"^internal\.acme\.com$"],
        banned_actions=["dos"],
    )
    rules = ScopeRules.from_target(target)
    assert rules.in_scope_regex == target.in_scope_regex
    assert rules.out_of_scope_regex == target.out_of_scope_regex
    assert rules.banned_actions == target.banned_actions

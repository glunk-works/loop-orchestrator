from dataclasses import dataclass

from loop_engine.personas.pm.fields import CHECKLIST_FIELDS

_SECURITY_FIELD = "security_and_risk_considerations"
_REGULATORY_SUPPLY_CHAIN_COST_FIELDS = (
    "regulatory_and_compliance_constraints",
    "supply_chain_security_expectations",
    "cost_sensitivity",
)
_MIN_TESTABLE_LENGTH = 10


@dataclass
class CriticFinding:
    field: str
    issue: str


def _is_blank(value: str) -> bool:
    return value.strip() == ""


def check_internal_consistency(spec: dict[str, str]) -> list[CriticFinding]:
    in_scope = spec.get("in_scope", "").strip()
    out_of_scope = spec.get("out_of_scope", "").strip()
    if in_scope and in_scope.upper() != "N/A" and in_scope.lower() == out_of_scope.lower():
        return [
            CriticFinding(
                field="in_scope",
                issue="in_scope and out_of_scope are identical, a contradiction.",
            )
        ]
    return []


def check_completeness(spec: dict[str, str]) -> list[CriticFinding]:
    findings = []
    for field_name in CHECKLIST_FIELDS:
        if _is_blank(spec.get(field_name, "")):
            findings.append(
                CriticFinding(
                    field=field_name,
                    issue="Field is blank; must be answered or explicitly marked N/A.",
                )
            )
    return findings


def check_acceptance_criteria_testable(spec: dict[str, str]) -> list[CriticFinding]:
    value = spec.get("acceptance_criteria", "").strip()
    if value and value.upper() != "N/A" and len(value) < _MIN_TESTABLE_LENGTH:
        return [
            CriticFinding(
                field="acceptance_criteria",
                issue="Acceptance criteria are too vague to be testable/verifiable.",
            )
        ]
    return []


def check_security_field_not_blank(spec: dict[str, str]) -> list[CriticFinding]:
    if _is_blank(spec.get(_SECURITY_FIELD, "")):
        return [
            CriticFinding(
                field=_SECURITY_FIELD,
                issue=(
                    "Security and risk considerations must be explicitly addressed, not left blank."
                ),
            )
        ]
    return []


def check_regulatory_supply_chain_cost_fields_not_blank(
    spec: dict[str, str],
) -> list[CriticFinding]:
    findings = []
    for field_name in _REGULATORY_SUPPLY_CHAIN_COST_FIELDS:
        if _is_blank(spec.get(field_name, "")):
            findings.append(
                CriticFinding(
                    field=field_name,
                    issue=(
                        f"{field_name} must be explicitly addressed (answered "
                        "or marked N/A), not silently left blank."
                    ),
                )
            )
    return findings


def review(spec: dict[str, str]) -> list[CriticFinding]:
    findings: list[CriticFinding] = []
    findings.extend(check_internal_consistency(spec))
    findings.extend(check_completeness(spec))
    findings.extend(check_acceptance_criteria_testable(spec))
    findings.extend(check_security_field_not_blank(spec))
    findings.extend(check_regulatory_supply_chain_cost_fields_not_blank(spec))
    return findings

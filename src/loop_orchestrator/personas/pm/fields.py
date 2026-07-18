# Matches pm_agent_loop.schema.project_spec.ProjectSpec's fields, excluding
# spec_version (not human-provided) and revision_history (populated by the
# critic revision loop, not asked of the human as a free-text question).
CHECKLIST_FIELDS: list[str] = [
    "problem_statement",
    "purpose_and_goals",
    "target_users",
    "in_scope",
    "out_of_scope",
    "functional_requirements",
    "integration_context",
    "acceptance_criteria",
    "priority_ranking",
    "timeline_and_cost_estimates",
    "risks_and_assumptions",
    "security_and_risk_considerations",
    "regulatory_and_compliance_constraints",
    "supply_chain_security_expectations",
    "cost_sensitivity",
    # open_questions_for_architect was retired in State schema v2: questions
    # are first-class State.questions entries routed by the engine's
    # escalation ladder, not free text trapped inside the spec.
]

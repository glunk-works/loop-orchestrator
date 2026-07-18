def test_public_api_exposes_expected_names() -> None:
    import loop_orchestrator

    assert hasattr(loop_orchestrator, "run_graph_loop")
    assert hasattr(loop_orchestrator, "State")
    assert hasattr(loop_orchestrator, "DEFAULT_LOOP")
    assert hasattr(loop_orchestrator, "LLMClient")

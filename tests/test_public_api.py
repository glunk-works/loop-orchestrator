def test_public_api_exposes_expected_names() -> None:
    import loop_engine

    assert hasattr(loop_engine, "run_graph_loop")
    assert hasattr(loop_engine, "State")
    assert hasattr(loop_engine, "DEFAULT_LOOP")
    assert hasattr(loop_engine, "LLMClient")

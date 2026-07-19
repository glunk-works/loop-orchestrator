"""Sanity checks on the packaged `inventory.sql` resource (§4 +
P0-D8/P0-D10): idempotent `CREATE ... IF NOT EXISTS` DDL, the four tables,
UUID PKs, the three natural-key UNIQUE constraints, `findings.run_id` as a
no-FK soft reference, the `validation_status` CHECK, and the array/JSONB
column types.
"""

from importlib import resources

SQL = resources.files("loop_orchestrator.tools.inventory_db").joinpath("inventory.sql").read_text()


def test_all_statements_are_idempotent_creates() -> None:
    statements = [s.strip() for s in SQL.split(";") if s.strip() and not s.strip().startswith("--")]
    assert statements
    for statement in statements:
        # Strip leading SQL comment lines before checking the statement start.
        body = "\n".join(
            line for line in statement.splitlines() if not line.strip().startswith("--")
        ).strip()
        assert body.upper().startswith("CREATE TABLE IF NOT EXISTS"), statement


def test_four_tables_present() -> None:
    for table in ("targets", "assets", "endpoints", "findings"):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in SQL


def test_uuid_primary_keys_with_gen_random_uuid() -> None:
    assert SQL.count("id UUID PRIMARY KEY DEFAULT gen_random_uuid()") == 4


def test_natural_key_unique_constraints() -> None:
    assert "program_name TEXT NOT NULL UNIQUE" in SQL
    assert "UNIQUE (target_id, asset_identifier)" in SQL
    assert "UNIQUE (asset_id, url_path)" in SQL


def test_findings_run_id_is_soft_ref_no_fk() -> None:
    start = SQL.index("CREATE TABLE IF NOT EXISTS findings")
    end = SQL.index(";", start)
    findings_block = SQL[start:end]
    run_id_line = next(line for line in findings_block.splitlines() if "run_id" in line)
    assert "run_id TEXT NOT NULL" in run_id_line
    assert "REFERENCES" not in run_id_line


def test_validation_status_check_constraint() -> None:
    assert "CHECK (validation_status IN ('unverified', 'ai_verified', 'human_verified'))" in SQL


def test_array_and_jsonb_columns() -> None:
    assert "in_scope_regex TEXT[]" in SQL
    assert "out_of_scope_regex TEXT[]" in SQL
    assert "banned_actions TEXT[]" in SQL
    assert "open_ports INT[]" in SQL
    assert "raw_scan_data JSONB" in SQL
    assert "http_methods TEXT[]" in SQL
    assert "tech_stack JSONB" in SQL


def test_no_langgraph_checkpoint_tables() -> None:
    assert "CREATE TABLE IF NOT EXISTS checkpoint" not in SQL.lower()

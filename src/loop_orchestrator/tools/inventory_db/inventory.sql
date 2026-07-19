-- Cross-run asset/finding inventory schema (bounty loop, §4).
--
-- Idempotent by construction (P0-D5): every statement is
-- `CREATE ... IF NOT EXISTS` so bootstrap() can run on every startup with no
-- migration tool. UUID primary keys (P0-D8) so IDs travel cleanly into JSON
-- run snapshots and the in-memory fake can mint identical uuid4() IDs.
-- `findings.run_id` is a plain-text soft reference to the producing run
-- snapshot -- deliberately no FK, since run snapshots live in JSON, never
-- Postgres. `validation_status` is TEXT + CHECK, not a native ENUM, so the
-- constraint stays inline in a clean `IF NOT EXISTS` create (P0-D10).
--
-- LangGraph's own checkpoint tables are not created here -- execution state
-- stays on JSON snapshots (§9-D1).

CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_name TEXT NOT NULL UNIQUE,
    in_scope_regex TEXT[],
    out_of_scope_regex TEXT[],
    banned_actions TEXT[]
);

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id UUID NOT NULL REFERENCES targets(id),
    asset_identifier TEXT NOT NULL,
    asset_type TEXT,
    open_ports INT[],
    raw_scan_data JSONB,
    UNIQUE (target_id, asset_identifier)
);

CREATE TABLE IF NOT EXISTS endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id),
    url_path TEXT NOT NULL,
    http_methods TEXT[],
    tech_stack JSONB,
    requires_auth BOOLEAN,
    UNIQUE (asset_id, url_path)
);

CREATE TABLE IF NOT EXISTS findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_id UUID NOT NULL REFERENCES endpoints(id),
    run_id TEXT NOT NULL,
    finding_type TEXT,
    severity TEXT,
    reproduction_steps TEXT,
    validation_status TEXT NOT NULL DEFAULT 'unverified'
        CHECK (validation_status IN ('unverified', 'ai_verified', 'human_verified'))
);

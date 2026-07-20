"""Security invariant (sprint 44 plan, item 1): every `cur.execute(...)` call
in `PsycopgInventory` passes a static string literal as its SQL text, never
an f-string/`%`-format/`.format()`/concatenation built from caller
arguments. This is the SQL-sink analog of fixed-argv/`shell=False` on the
five sanctioned subprocess surfaces -- checked here structurally rather than
by pattern-matching dangerous constructs, since "the first argument to
every execute() call is a plain `ast.Constant` string" is a stronger and
simpler guarantee than trying to enumerate every way a string *could* be
built dynamically.
"""

import ast
from pathlib import Path

PSYCOPG_IMPL = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "src"
    / "loop_orchestrator"
    / "tools"
    / "inventory_db"
    / "psycopg_impl.py"
)


def test_every_execute_call_passes_a_static_sql_literal() -> None:
    # bootstrap() is exempt: it applies inventory.sql's static packaged DDL
    # text (loaded via importlib.resources, not derived from any caller
    # argument -- bootstrap() takes none) through a local variable rather
    # than an inline literal. Every other method's execute() calls take
    # caller-supplied arguments as bound parameters only, so their SQL text
    # must be a literal.
    tree = ast.parse(PSYCOPG_IMPL.read_text(), filename=str(PSYCOPG_IMPL))
    class_def = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    checked_methods = [
        method
        for method in class_def.body
        if isinstance(method, ast.FunctionDef) and method.name != "bootstrap"
    ]
    execute_calls = [
        node
        for method in checked_methods
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "execute"
    ]
    assert execute_calls, "expected at least one cur.execute(...) call to check"
    for call in execute_calls:
        assert call.args, f"execute() call at line {call.lineno} has no SQL argument"
        sql_arg = call.args[0]
        assert isinstance(sql_arg, ast.Constant) and isinstance(sql_arg.value, str), (
            f"execute() call at line {call.lineno} in {PSYCOPG_IMPL.name} does not "
            "pass a static string literal as its SQL text -- all caller-supplied "
            "values must flow through the bound-parameters tuple, never the query "
            "string itself"
        )

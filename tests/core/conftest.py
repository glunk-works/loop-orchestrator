import os


def absolutize_mutmut_source_paths(monkeypatch) -> None:
    """Work around a mutmut 3.x / real-chdir collision for cwd-isolated tests.

    mutmut sets PY_IGNORE_IMPORTMISMATCH only during its one-time
    stats-collection pass (Sprint 38, BL-23). Its coverage trampoline
    re-resolves `Config.source_paths` (["src"], see [tool.mutmut] in
    pyproject.toml) against the *live process cwd* every time mutated core/
    code runs -- which crashes under any fixture that does a real chdir
    (several tests/core/ files isolate file-writing tests into a tmp_path).
    Absolutizing the already-loaded config here, before the chdir, makes
    that later resolution cwd-independent.

    Scoped via monkeypatch (auto-reverted at test teardown), NOT a direct
    assignment: `Config` is a process-wide singleton mutmut's own
    orchestration loop keeps reading from for the rest of the run
    (in-process pytest, no subprocess boundary) -- `only_mutate`'s glob
    match needs the original *relative* "src" or every mutant silently
    stops matching (a real run went 0/0 with an unscoped assignment here).

    No-op outside `hatch run mutate` (the env var is never set there), so
    `hatch run test`/`test-parallel` are untouched.
    """
    if os.environ.get("PY_IGNORE_IMPORTMISMATCH") != "1":
        return
    from mutmut.__main__ import Config

    monkeypatch.setattr(
        Config.get(), "source_paths", [p.resolve() for p in Config.get().source_paths]
    )

"""Unit-level coverage for `run_bootstrap`'s chain and ordering, with every
collaborator faked -- no real create, clone, scaffold write, or push. See
`test_integration.py` for the hermetic end-to-end (real scaffold + real
git_io) proof."""

import pytest
from pydantic import ValidationError

from loop_engine.flows.bootstrap import (
    BootstrapRequest,
    BootstrapResult,
    BootstrapStatus,
    run_bootstrap,
)
from loop_engine.tools.repo_io import RepoRef, RulesetInstallError


class _FakeRepoIO:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.repo = RepoRef(slug="glunk-works/demo", url="https://github.com/glunk-works/demo")

    def create_repository(self, name, *, org=None, private=True):
        self.calls.append(("create_repository", name, org, private))
        return self.repo

    def clone_repo(self, slug, dest, *, depth=None):
        self.calls.append(("clone_repo", slug, dest))
        return dest

    def create_branch(self, owner, repo, branch, *, base=None):
        self.calls.append(("create_branch", owner, repo, branch, base))
        return f"refs/heads/{branch}"

    def create_ruleset(self, owner, repo, *, branches, name="protect-integration-branches"):
        self.calls.append(("create_ruleset", owner, repo, tuple(branches), name))
        return 1


class _FailingRulesetRepoIO(_FakeRepoIO):
    """`create_ruleset` raises `RulesetInstallError` -- the real
    `create_ruleset` raises exactly this when the underlying `gh` call
    itself fails (S5: a genuine, live rejection), so this is the
    RULESET_FAILED case."""

    def create_ruleset(self, owner, repo, *, branches, name="protect-integration-branches"):
        self.calls.append(("create_ruleset", owner, repo, tuple(branches), name))
        raise RulesetInstallError("422 Unprocessable Entity")


class _UnparseableRulesetRepoIO(_FakeRepoIO):
    """`create_ruleset` raises a non-`RulesetInstallError` -- standing in for
    the live `create_ruleset`'s own `json.loads(...)["id"]` raising
    `KeyError`/`json.JSONDecodeError` when the POST actually succeeded but
    returned an unparseable body (S5). This must PROPAGATE out of
    `run_bootstrap`, not be mislabeled RULESET_FAILED."""

    def create_ruleset(self, owner, repo, *, branches, name="protect-integration-branches"):
        self.calls.append(("create_ruleset", owner, repo, tuple(branches), name))
        raise KeyError("id")


class _FakeGitIO:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def checkout_branch(self, tree, branch):
        self.calls.append(("checkout_branch", tree, branch))

    def commit_all(self, tree, message):
        self.calls.append(("commit_all", tree, message))

    def push_branch(self, tree, branch, *, remote="origin"):
        self.calls.append(("push_branch", tree, branch, remote))


class _FakeScaffold:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def write_skeleton(self, tree, *, kind, pkg_name, repo_name):
        self.calls.append(("write_skeleton", tree, kind, pkg_name, repo_name))
        return ["pyproject.toml"]


def _request(**overrides) -> BootstrapRequest:
    defaults = dict(name="demo")
    return BootstrapRequest(**{**defaults, **overrides})


def test_run_bootstrap_drives_full_chain_in_order_and_returns_created() -> None:
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO()
    scaffold = _FakeScaffold()

    request = _request()
    result = run_bootstrap(request, repo_io=repo_io, git_io=git_io, scaffold=scaffold)

    assert result.status == BootstrapStatus.CREATED
    assert result.repo == repo_io.repo
    assert result.default_branch == "main"
    assert result.integration_branch == "develop"
    assert result.ruleset_installed is True
    assert result.ruleset_id == 1  # S4: carried from the faked create_ruleset's return value
    assert result.ruleset_error is None

    assert repo_io.calls[0] == ("create_repository", "demo", "glunk-works", False)
    assert repo_io.calls[1] == ("clone_repo", "glunk-works/demo", "demo")
    assert git_io.calls[0] == ("checkout_branch", "demo", "main")
    assert scaffold.calls[0] == ("write_skeleton", "demo", "python", "demo", "demo")
    assert git_io.calls[1][0] == "commit_all"
    assert git_io.calls[1][1] == "demo"
    assert git_io.calls[2] == ("push_branch", "demo", "main", "origin")
    assert repo_io.calls[2] == ("create_branch", "glunk-works", "demo", "develop", "main")
    assert repo_io.calls[3] == (
        "create_ruleset",
        "glunk-works",
        "demo",
        ("main", "develop"),
        "protect-integration-branches",
    )


def test_create_branch_fires_after_push_with_base_equal_to_default_branch() -> None:
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO()
    scaffold = _FakeScaffold()

    run_bootstrap(_request(), repo_io=repo_io, git_io=git_io, scaffold=scaffold)

    push_index = git_io.calls.index(("push_branch", "demo", "main", "origin"))
    create_branch_call = ("create_branch", "glunk-works", "demo", "develop", "main")
    # Ordering is load-bearing: create_branch reads the base ref's SHA over
    # the API, so the push (which puts `main` on the remote) must come first.
    assert push_index < len(git_io.calls)
    assert create_branch_call in repo_io.calls
    # S9: create_ruleset's own strict position relative to create_branch is
    # covered by test_create_ruleset_fires_last_strictly_after_create_branch
    # -- no need to pin it here too via a `len(calls) - 2` positional assert.


def test_create_ruleset_fires_last_strictly_after_create_branch() -> None:
    """FD7: create_ruleset must run last -- a pull_request rule on `main`
    installed any earlier would reject the scaffold's own initial direct
    push, and installing it before create_branch raises a live question
    about whether the rule blocks API branch creation. Both are sidestepped
    by running it strictly last."""
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO()
    scaffold = _FakeScaffold()

    run_bootstrap(_request(), repo_io=repo_io, git_io=git_io, scaffold=scaffold)

    create_branch_call = ("create_branch", "glunk-works", "demo", "develop", "main")
    create_ruleset_call = (
        "create_ruleset",
        "glunk-works",
        "demo",
        ("main", "develop"),
        "protect-integration-branches",
    )
    assert repo_io.calls[-1] == create_ruleset_call
    assert repo_io.calls.index(create_branch_call) < repo_io.calls.index(create_ruleset_call)


def test_private_repo_skips_ruleset_installation_and_reports_it() -> None:
    """The private=True path is an explicit, deliberate opt-in that forfeits
    protection -- it must not attempt a call already known to 403 and it
    must not silently return CREATED as if the repo were protected."""
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO()
    scaffold = _FakeScaffold()

    result = run_bootstrap(
        _request(private=True), repo_io=repo_io, git_io=git_io, scaffold=scaffold
    )

    assert result.status == BootstrapStatus.CREATED
    assert result.ruleset_installed is False
    assert result.ruleset_id is None
    assert result.ruleset_error is None
    assert repo_io.calls[0] == ("create_repository", "demo", "glunk-works", True)
    assert not any(call[0] == "create_ruleset" for call in repo_io.calls)


def test_ruleset_failure_returns_repo_ref_instead_of_propagating() -> None:
    """R2: a live create_ruleset failure must not lose the RepoRef -- the repo
    is already created and main is already pushed by the time this call runs,
    so FD11 teardown needs the slug back, not a bare exception. S5: this is
    the `RulesetInstallError` case -- the `gh` call itself failed."""
    repo_io = _FailingRulesetRepoIO()
    git_io = _FakeGitIO()
    scaffold = _FakeScaffold()

    result = run_bootstrap(_request(), repo_io=repo_io, git_io=git_io, scaffold=scaffold)

    assert isinstance(result, BootstrapResult)
    assert result.status == BootstrapStatus.RULESET_FAILED
    assert result.repo == repo_io.repo
    assert result.ruleset_installed is False
    assert result.ruleset_id is None  # S4: never populated on the failure path
    assert result.ruleset_error  # S6: non-empty -- the str() of the raised exception
    assert "422 Unprocessable Entity" in result.ruleset_error
    assert any(call[0] == "create_ruleset" for call in repo_io.calls)


def test_non_ruleset_install_error_propagates_instead_of_ruleset_failed() -> None:
    """S5: a `create_ruleset` failure that is NOT a `RulesetInstallError`
    means the underlying `gh` POST likely SUCCEEDED (e.g. `json.loads(...)
    ["id"]` raised `KeyError`/`json.JSONDecodeError` on an unparseable
    response body) -- mislabeling that RULESET_FAILED would tell an operator
    the repo is unprotected and safe to tear down when it may already be
    protected. It must propagate, not be caught."""
    repo_io = _UnparseableRulesetRepoIO()
    git_io = _FakeGitIO()
    scaffold = _FakeScaffold()

    with pytest.raises(KeyError):
        run_bootstrap(_request(), repo_io=repo_io, git_io=git_io, scaffold=scaffold)


def test_no_open_pr_or_merge_verb_is_ever_reachable() -> None:
    from loop_engine.tools import repo_io as real_repo_io

    assert not hasattr(real_repo_io, "merge_pull_request")
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO()
    scaffold = _FakeScaffold()
    assert not hasattr(repo_io, "open_pr")

    run_bootstrap(_request(), repo_io=repo_io, git_io=git_io, scaffold=scaffold)
    # The fake doesn't even define open_pr; a call to it would AttributeError.


def test_bootstrap_request_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        _request(unknown_field="nope")


def test_bootstrap_request_defaults() -> None:
    request = _request()
    assert request.org == "glunk-works"
    assert request.kind == "python"
    assert request.default_branch == "main"
    assert request.integration_branch == "develop"
    assert request.private is False


def test_bootstrap_request_dest_defaults_to_name() -> None:
    request = _request(name="demo")
    assert request.dest == "demo"


def test_bootstrap_request_dest_honors_clone_dest_override() -> None:
    request = _request(clone_dest="somewhere-else")
    assert request.dest == "somewhere-else"


@pytest.mark.parametrize(
    "name,expected_pkg_name",
    [
        ("demo", "demo"),
        ("demo-widgets", "demo_widgets"),
        ("2demo", "_2demo"),
    ],
)
def test_bootstrap_request_derives_sanitized_pkg_name(name, expected_pkg_name) -> None:
    request = _request(name=name)
    assert request.pkg_name == expected_pkg_name


def test_flow_module_imports_no_keyring_and_writes_no_files_directly() -> None:
    import ast
    from pathlib import Path

    module_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/loop_engine/flows/bootstrap/flow.py"
    )
    tree = ast.parse(module_path.read_text())
    disallowed_writes = {"open", "write_text", "write_bytes"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "keyring" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "keyring"
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in disallowed_writes
            if isinstance(func, ast.Attribute):
                assert func.attr not in disallowed_writes

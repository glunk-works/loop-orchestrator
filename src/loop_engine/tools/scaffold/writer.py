"""Skeleton-writing module (the SECOND sanctioned file-write surface).

Writes a bootstrapped repo skeleton into a freshly cloned tree from bundled
package-data templates (`templates/`), rendering a dependency-free
`__PKG_NAME__` / `__REPO_NAME__` token substitution (`str.replace` — no
template-engine dependency). Mirrors `tools/git_io`'s carve-out precedent: a
new surface gets its own module, its own tests, and an honest boundary-count
bump — the file-write invariant becomes `{state_io, scaffold}` (see
`tests/tools/test_state_io_boundary.py`), while the four sanctioned
subprocess surfaces are unchanged (`scaffold` writes files; it does not
shell out — no `subprocess`/`keyring` import here).

Every `tree` argument is validated by reusing
`tools/repo_io/github.py::_validate_clone_dest` before any write — the same
discipline `tools/git_io` applies to its own `tree` argument. `pkg_name` is
sanitized to a safe Python identifier before it is ever used to build a
path, so a crafted repo name can never inject a `../` segment or a
non-identifier into the written tree.
"""

import re
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from loop_engine.tools.repo_io.github import _validate_clone_dest

_SCAFFOLD_PACKAGE = "loop_engine.tools.scaffold"
_TEMPLATES_DIR = "templates"
_CONVENTIONS_TEMPLATE = "CLAUDE.md"

_PKG_NAME_PLACEHOLDER = "__PKG_NAME__"
_REPO_NAME_PLACEHOLDER = "__REPO_NAME__"


def _sanitize_pkg_name(name: str) -> str:
    """Sanitize `name` to a safe Python identifier: replace anything outside
    `[A-Za-z0-9_]` with `_`, and prefix a leading digit with `_`. Raises
    `ValueError` if nothing salvageable remains (e.g. an empty or
    all-punctuation name)."""
    sanitized = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not sanitized.strip("_"):
        raise ValueError(f"Cannot derive a safe Python identifier from {name!r}")
    if sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    return sanitized


def _templates_root() -> Traversable:
    return resources.files(_SCAFFOLD_PACKAGE) / _TEMPLATES_DIR


def _walk_files(entry: Traversable, prefix: str = "") -> list[tuple[str, Traversable]]:
    found: list[tuple[str, Traversable]] = []
    for child in entry.iterdir():
        rel = f"{prefix}{child.name}"
        if child.is_dir():
            found.extend(_walk_files(child, prefix=f"{rel}/"))
        else:
            found.append((rel, child))
    return found


def _output_relpath(template_rel: str, *, pkg_name: str) -> Path:
    if template_rel == "gitignore.tmpl":
        return Path(".gitignore")
    if not template_rel.endswith(".tmpl"):
        raise ValueError(f"Unexpected non-template file in scaffold templates: {template_rel!r}")
    stripped = template_rel[: -len(".tmpl")]
    stripped = stripped.replace(_PKG_NAME_PLACEHOLDER, pkg_name)
    return Path(stripped)


def _write_rendered(dest: Path, rel_path: Path, content: str) -> None:
    target = dest / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_skeleton(tree: str, *, kind: str = "python", pkg_name: str, repo_name: str) -> list[str]:
    """Render `kind`'s bundled skeleton templates plus the shared
    conventions `CLAUDE.md` into the validated tree at `tree`. Returns the
    sorted list of relative paths written."""
    dest = _validate_clone_dest(tree)
    safe_pkg_name = _sanitize_pkg_name(pkg_name)

    written: list[str] = []
    kind_root = _templates_root() / kind
    for template_rel, entry in _walk_files(kind_root):
        out_rel = _output_relpath(template_rel, pkg_name=safe_pkg_name)
        content = (
            entry.read_text(encoding="utf-8")
            .replace(_PKG_NAME_PLACEHOLDER, safe_pkg_name)
            .replace(_REPO_NAME_PLACEHOLDER, repo_name)
        )
        _write_rendered(dest, out_rel, content)
        written.append(str(out_rel))

    conventions_text = (_templates_root() / _CONVENTIONS_TEMPLATE).read_text(encoding="utf-8")
    _write_rendered(dest, Path(_CONVENTIONS_TEMPLATE), conventions_text)
    written.append(_CONVENTIONS_TEMPLATE)

    return sorted(written)

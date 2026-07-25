"""The scope-validated recon dispatch surface (S47-D3): the input boundary
(`validate_target`-raise), and the `ReconDispatcher` protocol with its real
`gh`/hermetic-fake implementations. `tools/recon` is the third `gh`
subprocess-surface consumer, alongside `tools/issue_io` and `tools/repo_io`
-- the sanctioned surface count stays five
(`tests/tools/test_subprocess_surfaces.py`). Every function here takes its
`rules: ScopeRules` as a parameter (B5); this module never loads a target
itself.
"""

from loop_orchestrator.tools.recon.dispatch import (
    DispatchHandle,
    FakeReconDispatcher,
    GhReconDispatcher,
    ReconDispatcher,
    ReconDispatchFailedError,
    ReconTimeout,
    S3Key,
)
from loop_orchestrator.tools.recon.models import ReconRequest, build_recon_request

__all__ = [
    "DispatchHandle",
    "FakeReconDispatcher",
    "GhReconDispatcher",
    "ReconDispatchFailedError",
    "ReconDispatcher",
    "ReconRequest",
    "ReconTimeout",
    "S3Key",
    "build_recon_request",
]

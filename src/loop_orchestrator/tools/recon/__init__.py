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
from loop_orchestrator.tools.recon.parse import ReconPayloadError, ReconRecord, parse_jsonl
from loop_orchestrator.tools.recon.pipeline import IngestStats, ingest_batch

__all__ = [
    "DispatchHandle",
    "FakeReconDispatcher",
    "GhReconDispatcher",
    "IngestStats",
    "ReconDispatchFailedError",
    "ReconDispatcher",
    "ReconPayloadError",
    "ReconRecord",
    "ReconRequest",
    "ReconTimeout",
    "S3Key",
    "build_recon_request",
    "ingest_batch",
    "parse_jsonl",
]

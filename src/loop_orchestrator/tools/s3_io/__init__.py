"""S3 egress for the bounty loop's recon data path (S47-D3, P1-D5) -- the
sole `boto3` importer (`tests/tools/s3_io/test_boundary.py`). Provides the
`S3Fetcher` protocol fetching a dispatched recon run's result by its S3 key,
a real `boto3` implementation, and a hermetic in-memory fake.
"""

from loop_orchestrator.tools.s3_io.fetcher import (
    Boto3S3Fetcher,
    InMemoryS3Fetcher,
    S3Fetcher,
    S3ObjectNotFoundError,
)

__all__ = [
    "Boto3S3Fetcher",
    "InMemoryS3Fetcher",
    "S3Fetcher",
    "S3ObjectNotFoundError",
]

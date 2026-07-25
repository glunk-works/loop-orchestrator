"""`S3Fetcher` -- the `Protocol` `tools/recon`'s dispatch-await path uses to
retrieve a completed recon run's JSONL payload from S3 (S47-D8: the
correlation token is embedded in the object key, `recon/<token>.jsonl`).

`Boto3S3Fetcher` is the real implementation and this module's only `boto3`
import (`tests/tools/s3_io/test_boundary.py` pins this as the sole
permitted importer). Credentials ride boto3's default provider chain under
the already-declared AWS/Infisical-OIDC credential class
(docs/bounty_loop_architecture.md P1-D5) -- no keyring import, no new
credential path. `InMemoryS3Fetcher` is the hermetic fake: a canned
`{key: bytes}` store, so every other module's tests never touch the
network.
"""

from typing import Protocol

import boto3


class S3Fetcher(Protocol):
    def fetch(self, key: str) -> bytes: ...


class S3ObjectNotFoundError(Exception):
    """No object exists at `key` in `InMemoryS3Fetcher`'s canned store. The
    real `Boto3S3Fetcher` instead lets botocore's own `ClientError` (e.g.
    `NoSuchKey`) propagate unwrapped -- this is the fake's analog, not a
    shared exception type, since wrapping the real client's error would
    hide which AWS error code actually fired."""


class Boto3S3Fetcher:
    """Fetches a recon result object from S3. `bucket` and `region_name`
    are caller-supplied (wired from config by the CLI in a later task) --
    this module hardcodes neither."""

    def __init__(self, bucket: str, *, region_name: str | None = None) -> None:
        self._bucket = bucket
        self._client = boto3.client("s3", region_name=region_name)

    def fetch(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()


class InMemoryS3Fetcher:
    """Hermetic fake: `objects` is a canned `{key: bytes}` store."""

    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self._objects = dict(objects or {})

    def fetch(self, key: str) -> bytes:
        try:
            return self._objects[key]
        except KeyError:
            raise S3ObjectNotFoundError(f"no object at key {key!r}") from None

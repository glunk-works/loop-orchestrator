"""Hermetic tests for `tools/s3_io` (T1, Q2 -- the real client gets no live
coverage until the V-run). A `botocore.stub.Stubber` pins
`Boto3S3Fetcher`'s request shape (bucket/key/region) without any live AWS
call, and `InMemoryS3Fetcher` round-trips its canned bytes.
"""

import io

import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from loop_orchestrator.tools.s3_io.fetcher import (
    Boto3S3Fetcher,
    InMemoryS3Fetcher,
    S3ObjectNotFoundError,
)


def _streaming_body(data: bytes) -> StreamingBody:
    return StreamingBody(io.BytesIO(data), len(data))


def test_boto3_s3_fetcher_request_shape() -> None:
    fetcher = Boto3S3Fetcher("recon-bucket", region_name="us-east-1")
    stubber = Stubber(fetcher._client)
    stubber.add_response(
        "get_object",
        {"Body": _streaming_body(b"payload-bytes")},
        {"Bucket": "recon-bucket", "Key": "recon/abc123.jsonl"},
    )
    with stubber:
        result = fetcher.fetch("recon/abc123.jsonl")
    stubber.assert_no_pending_responses()
    assert result == b"payload-bytes"


def test_boto3_s3_fetcher_wires_region_into_the_client() -> None:
    fetcher = Boto3S3Fetcher("recon-bucket", region_name="eu-west-1")
    assert fetcher._client.meta.region_name == "eu-west-1"


def test_in_memory_s3_fetcher_round_trips_canned_bytes() -> None:
    fetcher = InMemoryS3Fetcher({"recon/tok.jsonl": b"canned-bytes"})
    assert fetcher.fetch("recon/tok.jsonl") == b"canned-bytes"


def test_in_memory_s3_fetcher_raises_on_a_missing_key() -> None:
    fetcher = InMemoryS3Fetcher()
    with pytest.raises(S3ObjectNotFoundError):
        fetcher.fetch("recon/missing.jsonl")

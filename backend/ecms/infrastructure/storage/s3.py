"""S3/MinIO object store adapter (SECTION 106).

Works with AWS S3 and any S3-compatible service such as MinIO via ``endpoint_url``. This
adapter requires a live service and is exercised through the Docker Compose stack rather
than unit tests.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from ecms.infrastructure.storage.object_store import ObjectInfo

__all__ = ["S3ObjectStore"]


class S3ObjectStore:
    """S3-compatible object store adapter."""

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        public_endpoint_url: str | None = None,
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        """Initialize the S3 client and target bucket."""
        self._bucket = bucket
        self._public_client = None
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                connect_timeout=2,
                read_timeout=5,
                retries={"mode": "standard", "total_max_attempts": 2},
            ),
        )
        if public_endpoint_url:
            self._public_client = boto3.client(
                "s3",
                endpoint_url=public_endpoint_url,
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=Config(signature_version="s3v4"),
            )

    def presign_get(self, key: str, *, expires_seconds: int = 300) -> str | None:
        """Return a short-lived browser URL when a public endpoint is configured."""
        if self._public_client is None:
            return None
        return str(
            self._public_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )
        )

    async def put_object(self, key: str, data: bytes) -> None:
        """Store bytes under a key."""
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
        )

    async def get_object(self, key: str) -> bytes:
        """Retrieve an object's bytes."""
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=self._bucket,
            Key=key,
        )
        body: bytes = response["Body"].read()
        return body

    async def delete_object(self, key: str) -> None:
        """Remove an object."""
        await asyncio.to_thread(
            self._client.delete_object,
            Bucket=self._bucket,
            Key=key,
        )

    async def list_objects(self, prefix: str = "") -> list[str]:
        """List keys under a prefix."""
        response = await asyncio.to_thread(
            self._client.list_objects_v2,
            Bucket=self._bucket,
            Prefix=prefix,
        )
        return [item["Key"] for item in response.get("Contents", [])]

    async def put_file(
        self,
        key: str,
        path: Path,
        *,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Upload a file using boto3's bounded multipart transfer path."""
        await asyncio.to_thread(
            self._client.upload_file,
            str(path),
            self._bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    async def stat_object(self, key: str) -> ObjectInfo:
        """Return object size, content type, and ETag."""
        response = await asyncio.to_thread(
            self._client.head_object,
            Bucket=self._bucket,
            Key=key,
        )
        return ObjectInfo(
            key=key,
            size=int(response["ContentLength"]),
            content_type=response.get("ContentType", "application/octet-stream"),
            etag=str(response.get("ETag", "")).strip('"') or None,
        )

    async def iter_object(
        self,
        key: str,
        *,
        chunk_size: int = 1024 * 1024,
        start: int = 0,
        end: int | None = None,
    ) -> AsyncIterator[bytes]:
        """Stream an S3 body in bounded chunks and close it reliably."""
        request: dict[str, object] = {"Bucket": self._bucket, "Key": key}
        if start or end is not None:
            request["Range"] = f"bytes={start}-{'' if end is None else end}"
        response = await asyncio.to_thread(
            self._client.get_object,
            **request,
        )
        body = response["Body"]
        try:
            while chunk := await asyncio.to_thread(body.read, chunk_size):
                yield bytes(chunk)
        finally:
            await asyncio.to_thread(body.close)

    async def ensure_bucket(self) -> None:
        """Create the configured bucket if it is absent."""
        try:
            await asyncio.to_thread(self._client.head_bucket, Bucket=self._bucket)
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            await asyncio.to_thread(self._client.create_bucket, Bucket=self._bucket)

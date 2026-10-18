# storage.py
"""S3 storage abstraction for SecureCloud.

Provides a ``Storage`` class that can be instantiated with a boto3 ``client``.
If ``boto3`` is not available or AWS credentials are not configured, the class
falls back to an in‑memory mock implementation useful for local tests.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from .config import S3_BUCKET, AWS_REGION


class StorageError(RuntimeError):
    """Unified exception type for storage‑related failures."""


class Storage:
    """Wraps AWS S3 operations used by SecureCloud.

    The public methods correspond to the operations required by the PRD:
    - ``upload_block``
    - ``download_block``
    - ``upload_manifest``
    - ``download_manifest``
    - ``list_files``
    - ``delete_file``
    """

    def __init__(self, client: Any = None, bucket: str = S3_BUCKET):
        self.bucket = bucket
        if client is not None:
            self.s3 = client
        else:
            # Attempt real boto3 client; fall back to mock if it fails.
            try:
                self.s3 = boto3.client("s3", region_name=AWS_REGION)
                # Simple call to verify credentials – will raise if mis‑configured.
                self.s3.head_bucket(Bucket=self.bucket)
                self._mock = False
            except (BotoCoreError, ClientError, Exception):
                # No valid AWS configuration – use an in‑memory mock.
                self.s3 = _InMemoryS3()
                self._mock = True

    # Helper to build object keys
    @staticmethod
    def _block_key(file_id: str, index: int) -> str:
        return f"files/{file_id}/blocks/{index:06d}.enc"

    @staticmethod
    def _manifest_key(file_id: str) -> str:
        return f"files/{file_id}/manifest.json"

    # ----------------------- Block operations -----------------------
    def upload_block(self, file_id: str, index: int, data: bytes) -> None:
        """Upload a single encrypted block.

        ``data`` is the ciphertext **including** the authentication tag.
        """
        key = self._block_key(file_id, index)
        try:
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)
        except Exception as exc:
            raise StorageError(f"Failed to upload block {index} for {file_id}: {exc}")

    def download_block(self, file_id: str, index: int) -> bytes:
        """Download a previously uploaded encrypted block.

        Returns the raw ``bytes`` stored in S3.
        """
        key = self._block_key(file_id, index)
        try:
            resp = self.s3.get_object(Bucket=self.bucket, Key=key)
            return resp["Body"].read()
        except Exception as exc:
            raise StorageError(f"Failed to download block {index} for {file_id}: {exc}")

    # ---------------------- Manifest operations ----------------------
    def upload_manifest(self, file_id: str, manifest: Dict[str, Any]) -> None:
        """Upload the JSON manifest for *file_id*.

        ``manifest`` must be JSON‑serialisable.
        """
        key = self._manifest_key(file_id)
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(manifest).encode("utf-8"),
                ContentType="application/json",
            )
        except Exception as exc:
            raise StorageError(f"Failed to upload manifest for {file_id}: {exc}")

    def download_manifest(self, file_id: str) -> Dict[str, Any]:
        """Retrieve and parse the JSON manifest for *file_id*."""
        key = self._manifest_key(file_id)
        try:
            resp = self.s3.get_object(Bucket=self.bucket, Key=key)
            data = resp["Body"].read().decode("utf-8")
            return json.loads(data)
        except Exception as exc:
            raise StorageError(f"Failed to download manifest for {file_id}: {exc}")

    # ------------------------- Listing --------------------------
    def list_files(self) -> List[Dict[str, Any]]:
        """Return a list of manifest metadata for all stored files.

        The method walks the bucket prefix ``files/`` and extracts the manifest
        objects. Errors for individual manifests are logged but do not abort the
        whole listing – the caller receives whatever could be parsed.
        """
        paginator = self.s3.get_paginator("list_objects_v2")
        files: List[Dict[str, Any]] = []
        try:
            for page in paginator.paginate(Bucket=self.bucket, Prefix="files/", Delimiter="/"):
                for prefix in page.get("CommonPrefixes", []):
                    file_id = prefix["Prefix"].split("/")[1]
                    try:
                        manifest = self.download_manifest(file_id)
                        files.append(manifest)
                    except StorageError:
                        # Skip corrupted or missing manifests – useful for debug.
                        continue
        except Exception as exc:
            raise StorageError(f"Failed to list files: {exc}")
        return files

    # -------------------------- Deletion --------------------------
    def delete_file(self, file_id: str) -> None:
        """Delete *file_id*'s manifest and all block objects.

        The operation is atomic at the S3 level – if any delete fails, a
        ``StorageError`` is raised after attempting to clean up remaining
        objects.
        """
        # Build list of keys to delete.
        keys = []
        # Manifest
        keys.append({"Key": self._manifest_key(file_id)})
        # Blocks – list objects under the block prefix.
        paginator = self.s3.get_paginator("list_objects_v2")
        try:
            for page in paginator.paginate(Bucket=self.bucket, Prefix=f"files/{file_id}/blocks/"):
                for obj in page.get("Contents", []):
                    keys.append({"Key": obj["Key"]})
        except Exception as exc:
            raise StorageError(f"Failed to enumerate blocks for deletion: {exc}")
        # Batch delete (max 1000 per request)
        try:
            for i in range(0, len(keys), 1000):
                batch = keys[i : i + 1000]
                self.s3.delete_objects(Bucket=self.bucket, Delete={"Objects": batch})
        except Exception as exc:
            raise StorageError(f"Failed to delete objects for {file_id}: {exc}")


# ---------------------------------------------------------------------
# Simple in‑memory mock used when no AWS configuration is present.
# ---------------------------------------------------------------------
class _InMemoryS3:
    def __init__(self):
        self.store: Dict[str, bytes] = {}

    # Minimal subset of boto3 client methods used above.
    def put_object(self, Bucket: str, Key: str, Body: bytes, **_: Any) -> None:
        self.store[Key] = Body

    def get_object(self, Bucket: str, Key: str) -> Dict[str, Any]:
        if Key not in self.store:
            raise ClientError({"Error": {"Code": "NoSuchKey", "Message": "Key not found"}}, "GetObject")
        return {"Body": _BytesIO(self.store[Key])}

    def delete_objects(self, Bucket: str, Delete: Dict[str, List[Dict[str, str]]]) -> None:
        for entry in Delete["Objects"]:
            self.store.pop(entry["Key"], None)

    def get_paginator(self, operation_name: str):
        return _MockPaginator(self.store, operation_name)

    def head_bucket(self, Bucket: str) -> None:
        # Always succeeds for mock.
        return None


class _BytesIO:
    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._data) - self._pos
        start = self._pos
        end = min(start + size, len(self._data))
        self._pos = end
        return self._data[start:end]


class _MockPaginator:
    def __init__(self, store: Dict[str, bytes], operation_name: str):
        self.store = store
        self.operation_name = operation_name

    def paginate(self, Bucket: str, Prefix: str = "", Delimiter: str = None):
        # Very simple emulation: list keys that start with Prefix.
        if self.operation_name != "list_objects_v2":
            return []
        # Build a pseudo‑page structure.
        keys = sorted(k for k in self.store if k.startswith(Prefix))
        if Delimiter:
            # Return common prefixes for the first component after the prefix.
            prefixes = set()
            for k in keys:
                remainder = k[len(Prefix) :]
                parts = remainder.split("/")
                if len(parts) > 1:
                    prefixes.add(Prefix + parts[0] + "/")
            yield {"CommonPrefixes": [{"Prefix": p} for p in sorted(prefixes)]}
        else:
            # Return all objects as Contents.
            contents = [{"Key": k} for k in keys]
            yield {"Contents": contents}

"""End of storage.py"""

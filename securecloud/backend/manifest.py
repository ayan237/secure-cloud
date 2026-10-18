# manifest.py
"""Utilities for building and validating the SecureCloud manifest.

The manifest is a JSON-serialisable dictionary stored alongside the encrypted
blocks in S3. It contains metadata required for reconstruction and for the
frontend to display file information.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Manifest:
    file_id: str
    filename: str
    file_size: int
    block_size: int
    block_count: int
    sha256: str
    created_at: str
    algorithm: str = "AES-256-GCM"
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for JSON serialisation."""
        return asdict(self)


def build_manifest(
    file_id: str,
    filename: str,
    file_size: int,
    block_size: int,
    block_count: int,
    sha256: str,
) -> Dict[str, Any]:
    """Create the manifest dictionary for a newly uploaded file.

    Parameters match the fields required by the PRD. ``created_at`` is an ISO‑8601
    timestamp in UTC.
    """
    manifest = Manifest(
        file_id=file_id,
        filename=filename,
        file_size=file_size,
        block_size=block_size,
        block_count=block_count,
        sha256=sha256,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    return manifest.to_dict()


def validate_manifest(data: Dict[str, Any]) -> None:
    """Validate that *data* contains the required keys and reasonable types.

    Raises ``ValueError`` with a helpful message if validation fails. The API
    layer catches this and turns it into a ``400 Bad Request`` response.
    """
    required_keys = {
        "file_id",
        "filename",
        "file_size",
        "block_size",
        "block_count",
        "sha256",
        "created_at",
    }
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(f"Manifest missing required fields: {', '.join(sorted(missing))}")
    # Basic type checks – more thorough validation could be added later.
    if not isinstance(data["file_id"], str) or not data["file_id"]:
        raise ValueError("Invalid file_id")
    if not isinstance(data["filename"], str) or not data["filename"]:
        raise ValueError("Invalid filename")
    if not isinstance(data["file_size"], int) or data["file_size"] < 0:
        raise ValueError("Invalid file_size")
    if not isinstance(data["block_size"], int) or data["block_size"] <= 0:
        raise ValueError("Invalid block_size")
    if not isinstance(data["block_count"], int) or data["block_count"] <= 0:
        raise ValueError("Invalid block_count")
    if not isinstance(data["sha256"], str) or len(data["sha256"]) != 64:
        raise ValueError("Invalid SHA-256 hash")
    # No return – successful validation is silent.

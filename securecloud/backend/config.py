# config.py
"""Configuration utilities for SecureCloud.
Loads environment variables from a .env file (if present) and provides
constants used throughout the backend.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root if it exists
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Required configuration – raise clear error if missing
AWS_REGION = os.getenv("AWS_REGION")
if not AWS_REGION:
    raise RuntimeError("AWS_REGION not set in environment or .env file")

S3_BUCKET = os.getenv("S3_BUCKET")
if not S3_BUCKET:
    raise RuntimeError("S3_BUCKET not set in environment or .env file")

# Optional configuration with sensible defaults
BLOCK_SIZE = int(os.getenv("BLOCK_SIZE", "1048576"))  # 1 MiB
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "20971520"))  # 20 MiB

# Local key store path (never committed to git)
KEY_STORE_DIR = PROJECT_ROOT / "securecloud_keys"
KEY_STORE_DIR.mkdir(parents=True, exist_ok=True)

def get_key_path(file_id: str) -> Path:
    """Return the path to the stored encryption key for a given file.
    The caller must ensure the directory exists.
    """
    return KEY_STORE_DIR / f"{file_id}.key"

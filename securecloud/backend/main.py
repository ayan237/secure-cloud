"""FastAPI entry point for SecureCloud.

Implements the API endpoints required by the PRD:
- GET /health
- POST /upload (multipart file upload)
- GET /files (list stored files)
- GET /files/{file_id}
- GET /files/{file_id}/download
- DELETE /files/{file_id}

The implementation uses the backend modules:
- `config` for configuration constants
- `encryption` for key handling and block encryption
- `file_utils` for segmentation
- `storage` for S3 (or mock) interaction
- `manifest` for manifest creation/parsing

Error handling follows the PRD: clear JSON error responses, proper HTTP status codes, and no leaking of internal details.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from pathlib import Path
import uuid
import hashlib
import json
import os

from .config import BLOCK_SIZE, MAX_UPLOAD_SIZE, get_key_path
from .encryption import generate_key, encrypt_block, decrypt_block
from .file_utils import split_file_into_blocks, cleanup_temp_dir
from .storage import Storage, StorageError
from .manifest import build_manifest, validate_manifest

app = FastAPI(title="SecureCloud API")

# Enable CORS for any origin (frontend may be served from a different port)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize storage (real S3 if credentials are present, otherwise mock)
storage = Storage()

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Basic validation
    if file.filename == "":
        raise HTTPException(status_code=400, detail="Empty filename")
    # Read file size (streaming to avoid loading whole file)
    temp_dir = Path("./temp_upload")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{uuid.uuid4()}_{file.filename}"
    size = 0
    with temp_path.open("wb") as out_f:
        while chunk := await file.read(1024 * 64):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                out_f.close()
                cleanup_temp_dir(temp_dir)
                raise HTTPException(status_code=413, detail="File exceeds maximum upload size")
            out_f.write(chunk)
    # Generate file ID and encryption key
    file_id = str(uuid.uuid4())
    key = generate_key()
    # Store key locally (never uploaded)
    key_path = get_key_path(file_id)
    key_path.write_bytes(key)
    # Compute SHA-256 of original file
    sha256 = hashlib.sha256()
    with temp_path.open("rb") as f:
        while data := f.read(1024 * 64):
            sha256.update(data)
    original_hash = sha256.hexdigest()
    # Split, encrypt, and upload each block
    block_count = 0
    for index, block in split_file_into_blocks(temp_path):
        nonce, ciphertext = encrypt_block(block, key)
        # Store nonce + ciphertext together (nonce is 12 bytes, prepend it)
        payload = nonce + ciphertext
        storage.upload_block(file_id, index, payload)
        block_count += 1
    # Build and upload manifest
    manifest = build_manifest(
        file_id=file_id,
        filename=file.filename,
        file_size=size,
        block_size=BLOCK_SIZE,
        block_count=block_count,
        sha256=original_hash,
    )
    storage.upload_manifest(file_id, manifest)
    # Cleanup temporary file
    cleanup_temp_dir(temp_dir)
    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": size,
        "block_count": block_count,
        "sha256": original_hash,
        "status": "uploaded",
    }

@app.get("/files")
def list_files():
    try:
        files = storage.list_files()
        return files
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/files/{file_id}")
def get_file_metadata(file_id: str):
    try:
        manifest = storage.download_manifest(file_id)
        return manifest
    except StorageError as exc:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/files/{file_id}/download")
def download_file(file_id: str):
    # Retrieve manifest
    try:
        manifest = storage.download_manifest(file_id)
    except StorageError:
        raise HTTPException(status_code=404, detail="File not found")
    # Load encryption key
    key_path = get_key_path(file_id)
    if not key_path.is_file():
        raise HTTPException(status_code=500, detail="Encryption key missing")
    key = key_path.read_bytes()

    # Reconstruct and authenticate blocks
    reconstructed_chunks = []
    sha256 = hashlib.sha256()
    for index in range(manifest["block_count"]):
        try:
            payload = storage.download_block(file_id, index)
            nonce = payload[:12]
            ciphertext = payload[12:]
            plaintext = decrypt_block(nonce, ciphertext, key)
            sha256.update(plaintext)
            reconstructed_chunks.append(plaintext)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Decryption or block retrieval failed: {str(exc)}")

    # Verify SHA-256 integrity against the manifest
    computed_hash = sha256.hexdigest()
    if computed_hash != manifest.get("sha256"):
        raise HTTPException(status_code=500, detail="SHA-256 integrity verification failed: hash mismatch")

    filename = manifest["filename"]
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/octet-stream",
    }
    return StreamingResponse(iter(reconstructed_chunks), headers=headers)

@app.delete("/files/{file_id}")
def delete_file(file_id: str):
    try:
        storage.delete_file(file_id)
        # Also delete local key file if present
        key_path = get_key_path(file_id)
        if key_path.is_file():
            key_path.unlink()
        return {"status": "deleted", "file_id": file_id}
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

import uuid
from backend.storage import Storage

def test_mock_storage_operations():
    storage = Storage()
    file_id = str(uuid.uuid4())
    
    data = b"Encrypted block content"
    storage.upload_block(file_id, 0, data)
    downloaded = storage.download_block(file_id, 0)
    assert downloaded == data
    
    manifest = {
        "file_id": file_id,
        "filename": "document.pdf",
        "file_size": 1024,
        "block_size": 1048576,
        "block_count": 1,
        "sha256": "abc123hash",
        "created_at": "2026-10-12T00:00:00Z"
    }
    storage.upload_manifest(file_id, manifest)
    downloaded_manifest = storage.download_manifest(file_id)
    assert downloaded_manifest["filename"] == "document.pdf"
    
    files = storage.list_files()
    assert any(f["file_id"] == file_id for f in files)
    
    storage.delete_file(file_id)
    files_after = storage.list_files()
    assert not any(f["file_id"] == file_id for f in files_after)

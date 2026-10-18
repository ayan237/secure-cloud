import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_upload_list_download_delete_cycle():
    content = b"Integration test sample payload for SecureCloud."
    files = {"file": ("test_upload.txt", io.BytesIO(content), "text/plain")}
    
    # 1. Upload
    res_upload = client.post("/upload", files=files)
    assert res_upload.status_code == 200
    upload_data = res_upload.json()
    file_id = upload_data["file_id"]
    assert upload_data["filename"] == "test_upload.txt"
    assert upload_data["status"] == "uploaded"
    
    # 2. List
    res_list = client.get("/files")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(item["file_id"] == file_id for item in items)
    
    # 3. Metadata
    res_meta = client.get(f"/files/{file_id}")
    assert res_meta.status_code == 200
    assert res_meta.json()["filename"] == "test_upload.txt"
    
    # 4. Download
    res_down = client.get(f"/files/{file_id}/download")
    assert res_down.status_code == 200
    assert res_down.content == content
    
    # 5. Delete
    res_del = client.delete(f"/files/{file_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"
    
    # Verify deleted
    res_meta_after = client.get(f"/files/{file_id}")
    assert res_meta_after.status_code == 404

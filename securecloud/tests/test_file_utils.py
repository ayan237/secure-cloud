import os
from pathlib import Path
from backend.file_utils import split_file_into_blocks, cleanup_temp_dir
from backend.config import BLOCK_SIZE

def test_split_file_into_blocks(tmp_path: Path):
    test_file = tmp_path / "sample.dat"
    content = b"X" * (BLOCK_SIZE * 2 + 500)
    test_file.write_bytes(content)
    
    blocks = list(split_file_into_blocks(test_file))
    assert len(blocks) == 3
    
    reconstructed = b"".join(chunk for idx, chunk in blocks)
    assert reconstructed == content
    assert blocks[0][0] == 0
    assert blocks[1][0] == 1
    assert blocks[2][0] == 2

def test_cleanup_temp_dir(tmp_path: Path):
    sub = tmp_path / "temp_folder"
    sub.mkdir()
    (sub / "test.txt").write_text("hello")
    assert sub.exists()
    
    cleanup_temp_dir(sub)
    assert not sub.exists()

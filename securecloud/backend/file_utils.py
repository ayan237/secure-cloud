# file_utils.py
"""Utility functions for handling file segmentation and temporary directories.

The module provides:
- :func:`split_file_into_blocks` – reads a file in binary mode and yields
  ``(block_index, block_bytes)`` tuples of exactly ``BLOCK_SIZE`` bytes,
  except for the final block which may be smaller.
- :func:`cleanup_temp_dir` – recursively removes a temporary directory used
  during upload/download operations.

Both functions are deliberately simple and avoid loading the entire file into
memory, which is important for large uploads.
"""

import os
import shutil
from pathlib import Path
from typing import Generator, Tuple

from .config import BLOCK_SIZE


def split_file_into_blocks(file_path: Path) -> Generator[Tuple[int, bytes], None, None]:
    """Yield binary blocks from *file_path*.

    Parameters
    ----------
    file_path: Path
        Path to the source file.

    Yields
    ------
    Tuple[int, bytes]
        ``(block_index, block_data)`` where ``block_data`` is at most
        ``BLOCK_SIZE`` bytes.
    """
    with file_path.open("rb") as f:
        index = 0
        while True:
            chunk = f.read(BLOCK_SIZE)
            if not chunk:
                break
            yield index, chunk
            index += 1


def cleanup_temp_dir(temp_dir: Path) -> None:
    """Recursively delete *temp_dir* if it exists.

    The function is tolerant of missing directories and any unexpected
    errors during removal are re‑raised to make debugging easier.
    """
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

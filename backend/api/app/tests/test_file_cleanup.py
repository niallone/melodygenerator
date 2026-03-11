"""Tests for the file cleanup service."""

import os
import time

from app.src.services.file_cleanup import cleanup_old_files


def test_cleanup_removes_old_files(tmp_path):
    old_file = tmp_path / "generated_melody_abc123.mid"
    old_file.write_text("old")
    # Set mtime to 2 days ago
    old_time = time.time() - 172800
    os.utime(old_file, (old_time, old_time))

    removed = cleanup_old_files(str(tmp_path), max_age=86400)
    assert removed == 1
    assert not old_file.exists()


def test_cleanup_keeps_recent_files(tmp_path):
    recent = tmp_path / "generated_melody_recent.wav"
    recent.write_text("new")

    removed = cleanup_old_files(str(tmp_path), max_age=86400)
    assert removed == 0
    assert recent.exists()


def test_cleanup_ignores_non_generated_files(tmp_path):
    other = tmp_path / "important_data.mid"
    other.write_text("keep")
    old_time = time.time() - 172800
    os.utime(other, (old_time, old_time))

    removed = cleanup_old_files(str(tmp_path), max_age=86400)
    assert removed == 0
    assert other.exists()


def test_cleanup_nonexistent_dir():
    removed = cleanup_old_files("/nonexistent/path")
    assert removed == 0

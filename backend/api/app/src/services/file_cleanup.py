"""Periodic cleanup of generated MIDI/WAV files."""

import logging
import os
import time

logger = logging.getLogger(__name__)

# Max age in seconds (24 hours)
MAX_FILE_AGE = 86400


def cleanup_old_files(output_dir: str, max_age: int = MAX_FILE_AGE) -> int:
    """Remove generated files older than max_age seconds.

    Returns:
        Number of files removed.
    """
    if not os.path.isdir(output_dir):
        return 0

    logger.debug(f"Running file cleanup on {output_dir}")
    now = time.time()
    removed = 0

    for filename in os.listdir(output_dir):
        if not filename.startswith("generated_melody_"):
            continue
        filepath = os.path.join(output_dir, filename)
        try:
            if now - os.path.getmtime(filepath) > max_age:
                os.remove(filepath)
                removed += 1
        except OSError as e:
            logger.warning(f"Failed to delete {filepath}: {e}")

    if removed:
        logger.info(f"Cleaned up {removed} old generated files from {output_dir}")
    return removed

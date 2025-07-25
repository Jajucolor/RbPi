#!/usr/bin/env python3
"""
Temporary File Cleanup Utility
Cleans up stuck temporary files from the speech system
"""

import os
import time
import tempfile
from pathlib import Path
import logging

def cleanup_temp_files():
    """Clean up temporary files with Windows compatibility"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Find temp directory
    temp_dir = Path(tempfile.gettempdir()) / "glasses_tts"
    
    if not temp_dir.exists():
        logger.info("No temporary directory found")
        return
    
    logger.info(f"Cleaning up temporary files in: {temp_dir}")
    
    files_cleaned = 0
    files_failed = 0
    
    for file in temp_dir.glob("*.mp3"):
        try:
            # Try to delete with retries
            for attempt in range(5):
                try:
                    if file.exists():
                        file.unlink()
                        logger.info(f"✅ Deleted: {file.name}")
                        files_cleaned += 1
                        break
                except PermissionError:
                    if attempt < 4:
                        wait_time = (attempt + 1) * 1.0
                        logger.info(f"⏳ File {file.name} still in use, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.warning(f"❌ Failed to delete {file.name} after 5 attempts")
                        files_failed += 1
                except Exception as e:
                    logger.warning(f"❌ Error deleting {file.name}: {e}")
                    files_failed += 1
                    break
                    
        except Exception as e:
            logger.error(f"❌ Unexpected error with {file.name}: {e}")
            files_failed += 1
    
    logger.info(f"🎉 Cleanup complete: {files_cleaned} files deleted, {files_failed} failed")
    
    if files_failed > 0:
        logger.info("💡 Tip: Restart your application to release file handles")

if __name__ == "__main__":
    cleanup_temp_files() 
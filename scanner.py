"""
Enhanced File Scanner Module
Discovers files and folders while extracting comprehensive metadata
"""

import os
import mimetypes
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import fnmatch


class FileScanner:
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)

        self.ignore_dirs = {
            "__pycache__",
            "node_modules",
            ".git",
            ".svn",
            "build",
            "dist",
            "target",
            ".cache",
            "tmp",
            "temp",
        }

        self.ignore_files = {".DS_Store", "Thumbs.db", "*.tmp", "*.cache", "*.log"}

    def scan(self) -> List[Dict[str, Any]]:
        """Scan the directory and return files with metadata"""
        items_to_organize = []

        print(f"Scanning directory: {self.root_path}")

        for item in self.root_path.rglob("*"):
            try:
                if item.is_file() and not self._should_ignore_file(item):
                    metadata = self._extract_file_metadata(item)
                    items_to_organize.append(metadata)

            except (PermissionError, OSError) as e:
                print(f"Error accessing {item}: {e}")
                continue

        return items_to_organize

    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract essential metadata from a file"""
        try:
            stat_info = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))

            metadata = {
                "path": str(file_path),
                "name": file_path.name,
                "suffix": file_path.suffix.lower(),
                "category": self._categorize_file(mime_type, file_path.suffix),
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "mime_type": mime_type,
            }

            return metadata

        except (PermissionError, OSError) as e:
            return {
                "path": str(file_path),
                "name": file_path.name,
                "error": str(e),
            }

    def _categorize_file(self, mime_type: str, suffix: str) -> str:
        """Categorize file based on MIME type and extension"""
        if not mime_type:
            # Fallback based on extension
            suffix = suffix.lower()
            if suffix in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".tiff",
                ".arw",
                ".cr2",
                ".cr3",
                ".nef",
                ".dng",
                ".orf",
                ".rw2",
            ]:
                return "image"
            elif suffix in [".mp4", ".avi", ".mkv", ".mov", ".wmv"]:
                return "video"
            elif suffix in [".mp3", ".wav", ".flac", ".aac", ".ogg"]:
                return "audio"
            elif suffix in [".txt", ".md", ".doc", ".docx", ".pdf"]:
                return "document"
            elif suffix in [".zip", ".rar", ".tar", ".gz", ".7z"]:
                return "archive"
            else:
                return "other"

        # MIME type based categorization
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type in ["application/pdf", "application/msword", "text/plain"]:
            return "document"
        elif mime_type.startswith("application/zip") or "archive" in mime_type:
            return "archive"
        else:
            return "other"

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        # Skip if in ignored directory
        for part in file_path.parts:
            if part in self.ignore_dirs:
                return True

        # Skip ignored files
        return any(
            fnmatch.fnmatch(file_path.name, pattern) for pattern in self.ignore_files
        )

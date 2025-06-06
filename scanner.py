"""
Enhanced File Scanner Module
Discovers files and folders while extracting comprehensive metadata
"""

import mimetypes
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import fnmatch


class FileScanner:
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)

        self.ignore_dirs = {
            # Version control
            ".git",
            ".svn",
            ".hg",
            # Python
            "__pycache__",
            ".venv",
            "venv",
            "env",
            ".pytest_cache",
            # Node.js
            "node_modules",
            ".npm",
            # Build/output
            "build",
            "dist",
            "target",
            "out",
            "bin",
            # IDE/Editor
            ".vscode",
            ".idea",
            ".vs",
            ".eclipse",
            # Cache/temp
            ".cache",
            "tmp",
            "temp",
            ".tmp",
            # Our organized files
            "organized_files",
        }

        # Focus on actual user files that need organization
        self.ignore_files = {
            ".DS_Store",
            "Thumbs.db",
            "*.tmp",
            "*.cache",
            "*.log",
        }

    def scan(self) -> List[Dict[str, Any]]:
        """
        Recursively scan the target directory and collect metadata for all files.

        Returns:
            A list of dictionaries containing metadata for each discovered file.

        Raises:
            FileNotFoundError: If the specified root path does not exist.
        """
        if not self.root_path.exists():
            raise FileNotFoundError(f"Path not found: {self.root_path.resolve()}")

        items_to_organize = []

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
            elif suffix in [
                ".txt",
                ".md",
                ".doc",
                ".docx",
                ".pdf",
                ".csv",
                ".py",
                ".js",
                ".sh",
                ".html",
                ".css",
            ]:
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
        elif mime_type in [
            "application/pdf",
            "application/msword",
            "text/plain",
            "text/csv",
            "text/x-shellscript",
            "application/x-sh",
            "text/x-python",
            "text/javascript",
            "text/html",
            "text/css",
        ]:
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

        # Skip if in a project directory (contains certain project files)
        if self._is_in_project_directory(file_path):
            return True

        # Skip ignored files
        return any(
            fnmatch.fnmatch(file_path.name, pattern) for pattern in self.ignore_files
        )

    def _is_in_project_directory(self, file_path: Path) -> bool:
        """Check if file is inside a project directory"""
        # Look for project indicators in parent directories
        current_dir = file_path.parent
        project_indicators = {
            "requirements.txt",
            "package.json",
            "setup.py",
            ".gitignore",
            ".git",
            ".venv",
            "venv",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
            "Makefile",
        }

        while current_dir != self.root_path and current_dir != current_dir.parent:
            # Check if this directory contains project files
            for indicator in project_indicators:
                if (current_dir / indicator).exists():
                    return True
            current_dir = current_dir.parent

        return False

"""
File Scanner Module
Discovers files and folders while respecting project boundaries
"""

import os
from pathlib import Path
from typing import List, Dict, Set
import fnmatch


class FileScanner:
    def __init__(self, root_path: Path):
        self.root_path = root_path

        # Project root markers
        self.project_markers = {
            ".git",
            "requirements.txt",
            "setup.py",
            "pyproject.toml",  # Python
            "package.json",
            "package-lock.json",
            "yarn.lock",  # JS/Node
            "next.config.js",
            "next.config.mjs",  # Next.js
            "vite.config.js",
            "vite.config.ts",  # Vite
            "tsconfig.json",  # TypeScript
            ".env",
            ".env.local",
            ".env.production",  # Environment files
        }

        # Directories to ignore
        self.ignore_dirs = {
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            "venv",
            "env",
            ".venv",
            "virtualenv",
            "dist",
            "build",
            ".next",
            ".nuxt",
            ".git",
            ".svn",
            ".hg",
            "files",  # Don't scan the files directory we're organizing into
        }

        # File patterns to ignore
        self.ignore_patterns = [
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "__pycache__",
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini",
            "*.log",
            "*.tmp",
            "*.temp",
            ".gitignore",
            ".dockerignore",
        ]

    def scan(self) -> List[Dict]:
        """Scan the directory and return files/folders to organize"""
        items_to_organize = []
        project_roots = self._find_project_roots()

        # Scan for items to organize
        for item in self.root_path.iterdir():
            if item.name.startswith(".") and item.name not in self.project_markers:
                # Hidden file outside of project
                if item.is_file():
                    items_to_organize.append(
                        {
                            "path": item,
                            "type": "hidden_file",
                            "size": item.stat().st_size,
                            "is_project": False,
                        }
                    )
                continue

            if item.is_dir():
                if self._is_project_root(item):
                    # This is a project directory - move as a whole
                    items_to_organize.append(
                        {
                            "path": item,
                            "type": "project",
                            "is_git": (item / ".git").exists(),
                            "size": self._get_dir_size(item),
                            "is_project": True,
                        }
                    )
                elif item.name not in self.ignore_dirs:
                    # Regular directory - scan its contents
                    items_to_organize.extend(self._scan_directory(item, project_roots))
            elif item.is_file():
                # File in root directory
                if not self._should_ignore_file(item):
                    items_to_organize.append(
                        {
                            "path": item,
                            "type": "file",
                            "size": item.stat().st_size,
                            "is_project": False,
                        }
                    )

        return items_to_organize

    def _find_project_roots(self) -> Set[Path]:
        """Find all project roots in the directory tree"""
        project_roots = set()

        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)

            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            # Check if this is a project root
            if self._is_project_root(root_path):
                project_roots.add(root_path)
                dirs.clear()  # Don't scan inside project directories

        return project_roots

    def _is_project_root(self, path: Path) -> bool:
        """Check if a directory is a project root"""
        if not path.is_dir():
            return False

        # Check for project markers
        for marker in self.project_markers:
            if (path / marker).exists():
                return True

        return False

    def _scan_directory(self, directory: Path, project_roots: Set[Path]) -> List[Dict]:
        """Scan a non-project directory for files to organize"""
        items = []

        try:
            for item in directory.rglob("*"):
                # Skip if inside a project root
                if any(
                    self._is_parent_path(proj_root, item) for proj_root in project_roots
                ):
                    continue

                # Skip ignored directories
                if item.is_dir() and item.name in self.ignore_dirs:
                    continue

                # Skip ignored files
                if item.is_file() and not self._should_ignore_file(item):
                    items.append(
                        {
                            "path": item,
                            "type": "file",
                            "size": item.stat().st_size,
                            "is_project": False,
                        }
                    )
        except PermissionError:
            pass

        return items

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored"""
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        return False

    def _is_parent_path(self, parent: Path, child: Path) -> bool:
        """Check if parent is a parent directory of child"""
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    def _get_dir_size(self, directory: Path) -> int:
        """Get total size of a directory"""
        total_size = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except (PermissionError, OSError):
            pass
        return total_size

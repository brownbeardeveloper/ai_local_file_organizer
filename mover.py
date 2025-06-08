"""
File Organizer Module
Safely copies or moves files and directories for organization
"""

import shutil
import os
from pathlib import Path
import hashlib


class FileMover:
    """
    File organization class that safely copies or moves files to structured directories.

    By default, files are copied (not moved) to preserve originals and allow safe testing
    of organization schemes. This non-destructive approach is recommended for most use cases.
    """

    def __init__(self, root_dir: str = ".", copy_mode: bool = True):
        """
        Initialize the FileMover with specified root directory and operation mode.

        Args:
            root_dir: Directory where organized files will be placed
            copy_mode: If True (default), copy files preserving originals.
                      If False, move files permanently (use with caution).

        Raises:
            FileNotFoundError: If root directory doesn't exist
            NotADirectoryError: If root_dir is not a directory
            PermissionError: If root directory is not writable
        """
        self.root_dir = Path(root_dir).resolve()
        self.copy_mode = copy_mode  # True for copy, False for move

        # Validate root directory exists
        if not self.root_dir.exists():
            raise FileNotFoundError(f"Root directory does not exist: {self.root_dir}")

        if not self.root_dir.is_dir():
            raise NotADirectoryError(f"Root path is not a directory: {self.root_dir}")

        if not os.access(self.root_dir, os.W_OK):
            raise PermissionError(f"Root directory is not writable: {self.root_dir}")

        # Directory structure mapping
        self.sub_dirs_map = {
            "documents": ["pdf", "word", "excel"],
            "finance": ["invoices", "receipts"],
            "work": ["projects", "other"],
            "studies": ["notes", "assignments"],
            "health": ["training", "insurance"],
            "photos": ["camera", "phone", "screenshots"],
            "software": ["installers", "configs"],
            "archives": ["zip", "rar"],
            "hidden": [],
            "large": [],
            "misc": [],
            "dev": ["python", "javascript", "java", "other"],
        }

        self._create_directory_structure()

    def organize_file(self, source_file_path: str, suggested_path: str) -> str:
        """Copy or move file based on pathplanner recommendation

        Returns:
            str: The actual final destination path where the file was placed
        """
        if not source_file_path:
            raise ValueError("Source file path cannot be empty")

        if not suggested_path:
            raise ValueError("Suggested path cannot be empty")

        source_path = Path(source_file_path)
        suggested_path_obj = Path(suggested_path)

        # Validate source file exists
        if not source_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {source_path}")

        # Validate source file permissions
        if not os.access(source_path, os.R_OK):
            raise PermissionError(f"Source file is not readable: {source_path}")

        # Validate source directory permissions (needed only for move operation)
        if not self.copy_mode and not os.access(source_path.parent, os.W_OK):
            raise PermissionError(
                f"Source directory is not writable: {source_path.parent}"
            )

        # Validate category
        self._validate_category(suggested_path_obj)

        # Validate file extension hasn't changed
        self._validate_extension(source_path, suggested_path_obj)

        # Convert suggested_path to be relative to root_dir
        destination_path = self.root_dir / suggested_path_obj

        if self.copy_mode:
            return self.copy(str(source_path), str(destination_path))
        else:
            return self.move(str(source_path), str(destination_path))

    def _create_directory_structure(self):
        """Create the required directory structure in root_dir"""
        for main_category, sub_categories in self.sub_dirs_map.items():
            main_path = self.root_dir / main_category
            main_path.mkdir(parents=True, exist_ok=True)

            for sub_category in sub_categories:
                sub_path = main_path / sub_category
                sub_path.mkdir(parents=True, exist_ok=True)

    def _validate_category(self, suggested_path: Path):
        """Validate that the suggested path uses a valid category"""
        if not suggested_path.parts:
            raise RuntimeError("Suggested path is empty")

        main_category = suggested_path.parts[0]
        if main_category not in self.sub_dirs_map:
            valid_categories = list(self.sub_dirs_map.keys())
            raise RuntimeError(
                f"Invalid category '{main_category}'. Valid categories: {valid_categories}"
            )

        # Check subcategory if it exists
        if len(suggested_path.parts) > 1:
            sub_category = suggested_path.parts[1]
            valid_sub_categories = self.sub_dirs_map[main_category]
            if valid_sub_categories and sub_category not in valid_sub_categories:
                raise RuntimeError(
                    f"Invalid subcategory '{sub_category}' for category '{main_category}'. Valid subcategories: {valid_sub_categories}"
                )

    def _validate_extension(self, source_path: Path, suggested_path: Path):
        """Validate that the file extension is not changed during organization"""
        source_suffix = source_path.suffix.lower()
        suggested_suffix = suggested_path.suffix.lower()

        if source_suffix != suggested_suffix:
            raise ValueError(
                f"File extension cannot be changed during organization. "
                f"Source: '{source_suffix}', Suggested: '{suggested_suffix}'. "
                f"File extensions must remain the same to preserve file type and compatibility."
            )

    def move(self, source: str, destination: str) -> str:
        """Move a file or directory to a new location

        Returns:
            str: The actual final destination path where the file was moved
        """
        if not source:
            raise ValueError("Source path cannot be empty")

        if not destination:
            raise ValueError("Destination path cannot be empty")

        source_path = Path(source)
        destination_path = Path(destination)

        # Validate source exists
        if not source_path.exists():
            raise FileNotFoundError(f"Source does not exist: {source_path}")

        # Validate source permissions
        if source_path.is_file() and not os.access(source_path, os.R_OK):
            raise PermissionError(f"Source file is not readable: {source_path}")
        elif source_path.is_dir() and not os.access(source_path, os.R_OK | os.X_OK):
            raise PermissionError(f"Source directory is not accessible: {source_path}")

        # Validate source directory permissions (needed only for move operation)
        if not os.access(source_path.parent, os.W_OK):
            raise PermissionError(
                f"Source parent directory is not writable: {source_path.parent}"
            )

        # Validate destination directory permissions (will be created if needed)
        dest_parent = destination_path.parent
        while not dest_parent.exists() and dest_parent != dest_parent.parent:
            dest_parent = dest_parent.parent
        if dest_parent.exists() and not os.access(dest_parent, os.W_OK):
            raise PermissionError(
                f"Destination directory is not writable: {dest_parent}"
            )

        try:
            # Create destination directory if it doesn't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Handle naming conflicts
            final_destination = self._handle_conflicts(destination_path)

            # Calculate hash for verification (only for files)
            source_hash = None
            if (
                source_path.is_file() and source_path.stat().st_size < 100 * 1024 * 1024
            ):  # Only hash files < 100MB
                source_hash = self._calculate_hash(source_path)

            # Perform the move
            if source_path.is_dir():
                # Move entire directory
                shutil.move(str(source_path), str(final_destination))
            else:
                # Move file
                shutil.move(str(source_path), str(final_destination))

            # Verify move (for files)
            if source_hash and final_destination.is_file():
                dest_hash = self._calculate_hash(final_destination)
                if source_hash != dest_hash:
                    raise RuntimeError("File hash mismatch after move!")

            return str(final_destination)

        except Exception as e:
            raise RuntimeError(
                f"Failed to move {source_path} to {destination_path}: {str(e)}"
            )

    def _handle_conflicts(self, destination: Path) -> Path:
        """Add sequential numbers to files (person2.jpg, person3.jpg, etc.)"""
        if not destination.exists():
            return destination

        counter = 2

        # For files, add number before extension
        if destination.is_file() or "." in destination.name:
            stem = destination.stem
            suffix = destination.suffix
            parent = destination.parent

            while True:
                new_name = f"{stem}{counter}{suffix}"
                new_path = parent / new_name
                if not new_path.exists():
                    return new_path
                counter += 1
        else:
            # For directories
            while True:
                new_path = destination.parent / f"{destination.name}{counter}"
                if not new_path.exists():
                    return new_path
                counter += 1

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def copy(self, source: str, destination: str) -> str:
        """Copy a file or directory to a new location, preserving the original

        Returns:
            str: The actual final destination path where the file was copied
        """
        if not source:
            raise ValueError("Source path cannot be empty")

        if not destination:
            raise ValueError("Destination path cannot be empty")

        source_path = Path(source)
        destination_path = Path(destination)

        # Validate source exists
        if not source_path.exists():
            raise FileNotFoundError(f"Source does not exist: {source_path}")

        # Validate source permissions
        if source_path.is_file() and not os.access(source_path, os.R_OK):
            raise PermissionError(f"Source file is not readable: {source_path}")
        elif source_path.is_dir() and not os.access(source_path, os.R_OK | os.X_OK):
            raise PermissionError(f"Source directory is not accessible: {source_path}")

        # Validate destination directory permissions (will be created if needed)
        dest_parent = destination_path.parent
        while not dest_parent.exists() and dest_parent != dest_parent.parent:
            dest_parent = dest_parent.parent
        if dest_parent.exists() and not os.access(dest_parent, os.W_OK):
            raise PermissionError(
                f"Destination directory is not writable: {dest_parent}"
            )

        try:
            # Create destination directory if it doesn't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Handle naming conflicts
            final_destination = self._handle_conflicts(destination_path)

            # Calculate hash for verification (only for files)
            source_hash = None
            if (
                source_path.is_file() and source_path.stat().st_size < 100 * 1024 * 1024
            ):  # Only hash files < 100MB
                source_hash = self._calculate_hash(source_path)

            # Perform the copy
            if source_path.is_dir():
                # Copy entire directory tree
                shutil.copytree(str(source_path), str(final_destination))
            else:
                # Copy file
                shutil.copy2(str(source_path), str(final_destination))

            # Verify copy (for files)
            if source_hash and final_destination.is_file():
                dest_hash = self._calculate_hash(final_destination)
                if source_hash != dest_hash:
                    raise RuntimeError("File hash mismatch after copy!")

            return str(final_destination)

        except Exception as e:
            raise RuntimeError(
                f"Failed to copy {source_path} to {destination_path}: {str(e)}"
            )

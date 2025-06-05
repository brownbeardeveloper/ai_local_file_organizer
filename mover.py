"""
File Mover Module
Safely moves files and directories with logging
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import hashlib


class FileMover:
    def __init__(self):
        self.move_log = []
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        self.log_file = logs_dir / "file_organizer.json"
        self._load_log()

    def organize_file(self, file_analysis: Dict, suggested_path: Path) -> bool:
        """Move file based on suggester recommendation"""
        if not suggested_path:
            return False

        source_path = Path(file_analysis["path"])
        return self.move(source_path, suggested_path)

    def move(self, source: Path, destination: Path) -> bool:
        """Move a file or directory to a new location"""
        try:
            # Create destination directory if it doesn't exist
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Handle naming conflicts
            final_destination = self._handle_conflicts(destination)

            # Calculate hash for verification (only for files)
            source_hash = None
            if (
                source.is_file() and source.stat().st_size < 100 * 1024 * 1024
            ):  # Only hash files < 100MB
                source_hash = self._calculate_hash(source)

            # Perform the move
            if source.is_dir():
                # Move entire directory
                shutil.move(str(source), str(final_destination))
            else:
                # Move file
                shutil.move(str(source), str(final_destination))

            # Verify move (for files)
            if source_hash and final_destination.is_file():
                dest_hash = self._calculate_hash(final_destination)
                if source_hash != dest_hash:
                    raise Exception("File hash mismatch after move!")

            # Log the move
            self._log_move(source, final_destination, source_hash)

            return True

        except Exception as e:
            raise Exception(f"Failed to move {source} to {destination}: {str(e)}")

    def _handle_conflicts(self, destination: Path) -> Path:
        """Add sequential numbers to all files (001, 002, etc.)"""
        # For files, add 3-digit number before extension
        if destination.is_file() or "." in destination.name:
            stem = destination.stem
            suffix = destination.suffix
            parent = destination.parent

            counter = 1
            while True:
                new_name = f"{stem}_{counter:03d}{suffix}"
                new_path = parent / new_name
                if not new_path.exists():
                    return new_path
                counter += 1
        else:
            # For directories
            counter = 1
            while True:
                new_path = destination.parent / f"{destination.name}_{counter:03d}"
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

    def _log_move(self, source: Path, destination: Path, file_hash: str = None):
        """Log the move operation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": str(source),
            "destination": str(destination),
            "file_hash": file_hash,
            "size": source.stat().st_size if source.exists() else None,
        }

        self.move_log.append(log_entry)
        self._save_log()

    def _load_log(self):
        """Load existing move log"""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    data = json.load(f)
                    self.move_log = data.get("moves", [])
            except:
                self.move_log = []

    def _save_log(self):
        """Save move log to file"""
        try:
            log_data = {"version": "1.0", "moves": self.move_log}

            with open(self.log_file, "w") as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save log: {e}")

    def get_recent_moves(self, count: int = 10) -> List[Dict]:
        """Get recent move operations"""
        return self.move_log[-count:] if self.move_log else []

    def undo_last_move(self) -> bool:
        """Undo the last move operation (if possible)"""
        if not self.move_log:
            return False

        last_move = self.move_log[-1]
        source = Path(last_move["source"])
        destination = Path(last_move["destination"])

        try:
            if destination.exists() and not source.exists():
                shutil.move(str(destination), str(source))
                self.move_log.pop()
                self._save_log()
                return True
        except Exception:
            pass

        return False

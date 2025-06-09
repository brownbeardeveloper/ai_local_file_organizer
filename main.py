#!/usr/bin/env python3
"""AI File Organizer - Clean and simple file organization"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from scanner import FileScanner
from analyzer import FileAnalyzer
from openai_suggester import OpenAIPathPlanner
from mover import FileMover


class FileOrganizer:
    """
    Orchestrates the file organization process using AI analysis and intelligent path planning.

    Follows Single Responsibility Principle by focusing solely on coordinating the
    scanning, analysis, planning, and moving phases of file organization.
    """

    def __init__(
        self,
        scanner: FileScanner,
        analyzer: FileAnalyzer,
        path_planner: OpenAIPathPlanner,
        mover: FileMover,
    ):
        """
        Initialize the file organizer with required components.

        Args:
            scanner: File discovery component
            analyzer: AI-powered file analysis component
            path_planner: AI-powered path suggestion component
            mover: File moving/copying component

        Raises:
            TypeError: If any component is None or of wrong type
        """
        if not all([scanner, analyzer, path_planner, mover]):
            raise TypeError(
                "All components (scanner, analyzer, path_planner, mover) are required"
            )

        self.scanner = scanner
        self.analyzer = analyzer
        self.path_planner = path_planner
        self.mover = mover

    def organize(self) -> Dict[str, Any]:
        """
        Execute the complete file organization workflow.

        Returns:
            Dict containing organization results and statistics

        Raises:
            RuntimeError: If any critical step fails
        """
        # Phase 1: File Discovery
        files = self._discover_files()
        if not files:
            return {
                "success": True,
                "message": "No files found to organize",
                "organized_count": 0,
                "total_count": 0,
            }

        # Phase 2: Content Analysis
        analyses = self._analyze_files(files)
        if not analyses:
            return {
                "success": False,
                "message": "No files could be analyzed",
                "organized_count": 0,
                "total_count": len(files),
            }

        # Phase 3: Path Planning
        path_suggestions = self._plan_organization(analyses)
        if not path_suggestions:
            return {
                "success": False,
                "message": "No path suggestions generated",
                "organized_count": 0,
                "total_count": len(files),
            }

        # Phase 4: File Organization
        results = self._execute_organization(analyses, path_suggestions)

        return {
            "success": True,
            "message": f"Organization complete! Organized {results['organized_count']}/{results['total_count']} files",
            "organized_count": results["organized_count"],
            "total_count": results["total_count"],
            "skipped_files": results["skipped_files"],
            "error_files": results["error_files"],
        }

    def _discover_files(self) -> List[Dict[str, Any]]:
        """Discover files to be organized."""
        print("Scanning files...")
        try:
            files = self.scanner.scan()
            print(f"Found {len(files)} files")
            return files
        except Exception as e:
            raise RuntimeError(f"File discovery failed: {e}")

    def _analyze_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze file contents using AI."""
        print("Analyzing files...")
        analyses = []

        for file_info in files:
            try:
                analysis = self.analyzer.analyze(file_info)
                analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing {file_info['name']}: {e}")
                continue

        print(f"Successfully analyzed {len(analyses)}/{len(files)} files")
        return analyses

    def _plan_organization(self, analyses: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate organization path suggestions."""
        print("Planning organization...")
        try:
            path_suggestions = self.path_planner.suggest_paths(analyses)
            print(f"Generated {len(path_suggestions)} path suggestions")
            return path_suggestions
        except Exception as e:
            raise RuntimeError(f"Path planning failed: {e}")

    def _execute_organization(
        self, analyses: List[Dict[str, Any]], path_suggestions: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute the file organization based on suggestions."""
        print("Planning file organization...")

        # Phase 1: Collect and validate all planned moves
        planned_moves = []
        skipped_files = []
        planned_destinations = set()  # Track planned destinations to avoid conflicts

        for analysis in analyses:
            original_path = analysis["path"]
            suggested_path = path_suggestions.get(original_path)

            if not suggested_path:
                skipped_files.append(
                    {"name": analysis["name"], "reason": "no path suggestion"}
                )
                continue

            # Pre-validate the move to get the final destination path
            try:
                final_destination = self.mover._get_final_destination(
                    original_path, suggested_path
                )

                # Handle conflicts with other planned moves
                final_destination = self._resolve_planning_conflicts(
                    final_destination, planned_destinations
                )

                planned_moves.append(
                    {
                        "analysis": analysis,
                        "original_path": original_path,
                        "final_destination": final_destination,
                    }
                )
                planned_destinations.add(final_destination)
            except Exception as e:
                skipped_files.append(
                    {"name": analysis["name"], "reason": f"path validation failed: {e}"}
                )

        # Phase 2: Show planned moves and get user confirmation
        if not planned_moves:
            print("No valid moves to execute.")
            return {
                "organized_count": 0,
                "total_count": len(analyses),
                "skipped_files": skipped_files,
                "error_files": [],
            }

        print(f"\nPlanned file organization ({len(planned_moves)} files):")
        print("=" * 80)
        for move in planned_moves:
            original_full_path = Path(move["original_path"]).resolve()
            final_full_path = Path(move["final_destination"]).resolve()
            print(f"{original_full_path}")
            print(f"  -> {final_full_path}")
            print()

        # Get user confirmation
        while True:
            response = input("Proceed with file organization? (Y/N): ").strip().upper()
            if response in ["Y", "YES"]:
                break
            elif response in ["N", "NO"]:
                print("File organization cancelled by user.")
                return {
                    "organized_count": 0,
                    "total_count": len(analyses),
                    "skipped_files": skipped_files
                    + [
                        {
                            "name": move["analysis"]["name"],
                            "reason": "cancelled by user",
                        }
                        for move in planned_moves
                    ],
                    "error_files": [],
                }
            else:
                print("Please enter Y (yes) or N (no)")

        # Phase 3: Execute the approved moves
        print("\nExecuting file organization...")
        organized_count = 0
        error_files = []

        for move in planned_moves:
            analysis = move["analysis"]
            original_path = move["original_path"]

            try:
                final_destination = self.mover.organize_file(
                    original_path, path_suggestions[original_path]
                )
                if final_destination:
                    final_full_path = Path(final_destination).resolve()
                    original_full_path = Path(original_path).resolve()
                    print(f"{original_full_path} -> {final_full_path}")
                    organized_count += 1
                else:
                    error_files.append(
                        {"name": analysis["name"], "reason": "move operation failed"}
                    )
                    print(f"Failed to organize {analysis['name']}")
            except Exception as e:
                error_files.append({"name": analysis["name"], "reason": str(e)})
                print(f"Error organizing {analysis['name']}: {e}")

        return {
            "organized_count": organized_count,
            "total_count": len(analyses),
            "skipped_files": skipped_files,
            "error_files": error_files,
        }

    def _resolve_planning_conflicts(
        self, destination_path: str, planned_destinations: set
    ) -> str:
        """
        Resolve conflicts between planned moves by adding sequential numbers.
        Checks both existing files and other planned destinations.

        Args:
            destination_path: The initially planned destination path
            planned_destinations: Set of already planned destination paths

        Returns:
            str: A unique destination path that doesn't conflict with existing files or planned moves
        """
        path_obj = Path(destination_path)

        # If no conflict with planned destinations and file doesn't exist, use as-is
        if destination_path not in planned_destinations and not path_obj.exists():
            return destination_path

        # Extract path components for sequential numbering
        stem = path_obj.stem
        suffix = path_obj.suffix
        parent = path_obj.parent

        # Find ALL existing files with this stem pattern
        existing_numbers = set()
        if parent.exists():
            for existing_file in parent.glob(f"{stem}*{suffix}"):
                name = existing_file.stem
                if name == stem:
                    existing_numbers.add(1)  # Base file counts as 1
                elif name.startswith(stem) and name[len(stem) :].isdigit():
                    number = int(name[len(stem) :])
                    existing_numbers.add(number)

        # Find ALL planned files with this stem pattern
        for planned_path in planned_destinations:
            planned_obj = Path(planned_path)
            if planned_obj.parent == parent and planned_obj.suffix == suffix:
                planned_name = planned_obj.stem
                if planned_name == stem:
                    existing_numbers.add(1)  # Base file counts as 1
                elif (
                    planned_name.startswith(stem)
                    and planned_name[len(stem) :].isdigit()
                ):
                    number = int(planned_name[len(stem) :])
                    existing_numbers.add(number)

        # Find the next available sequential number
        counter = 2
        while counter in existing_numbers:
            counter += 1

        new_name = f"{stem}{counter}{suffix}"
        return str(parent / new_name)


def create_organizer(
    source_dir: Optional[Path] = None,
    target_dir: Optional[Path] = None,
    copy_mode: bool = True,
) -> FileOrganizer:
    """
    Factory function to create a FileOrganizer with default configuration.

    Args:
        source_dir: Source directory to scan (defaults to ./unorganized_files)
        target_dir: Target directory for organized files (defaults to ./organized_files)
        copy_mode: Whether to copy files (True) or move them (False)

    Returns:
        Configured FileOrganizer instance

    Raises:
        FileNotFoundError: If source directory doesn't exist
        RuntimeError: If component initialization fails
    """
    root_path = Path(".").resolve()

    if source_dir is None:
        source_dir = root_path / "unorganized_files"
    if target_dir is None:
        target_dir = root_path / "organized_files"

    try:
        scanner = FileScanner(source_dir)
        analyzer = FileAnalyzer()
        path_planner = OpenAIPathPlanner()
        mover = FileMover(root_dir=str(target_dir), copy_mode=copy_mode)

        return FileOrganizer(scanner, analyzer, path_planner, mover)
    except Exception as e:
        raise RuntimeError(f"Failed to create file organizer: {e}")


def main():
    """Main entry point for the file organization application."""
    try:
        organizer = create_organizer()
        results = organizer.organize()

        print(f"\n{results['message']}")
        if results.get("error_files"):
            print(f"Files with errors: {len(results['error_files'])}")
        if results.get("skipped_files"):
            print(f"Files skipped: {len(results['skipped_files'])}")

    except Exception as e:
        print(f"Application failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

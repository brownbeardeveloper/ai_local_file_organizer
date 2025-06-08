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
        print("Organizing files...")

        organized_count = 0
        skipped_files = []
        error_files = []

        for analysis in analyses:
            original_path = analysis["path"]
            suggested_path = path_suggestions.get(original_path)

            if not suggested_path:
                skipped_files.append(
                    {"name": analysis["name"], "reason": "no path suggestion"}
                )
                print(f"Skipped {analysis['name']} (no path suggestion)")
                continue

            try:
                final_destination = self.mover.organize_file(
                    original_path, suggested_path
                )
                if final_destination:
                    final_name = Path(final_destination).name
                    print(f"{analysis['name']} -> {final_name}")
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

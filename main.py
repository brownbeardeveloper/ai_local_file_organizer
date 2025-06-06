#!/usr/bin/env python3
"""AI File Organizer - Clean and simple file organization"""

from pathlib import Path
from scanner import FileScanner
from analyzer import FileAnalyzer
from suggester import PathSuggester
from mover import FileMover


def main():
    root_path = Path(".").resolve()
    unstructed_files_path = root_path / "unstructed_files"
    organized_files_path = root_path / "organized_files"

    scanner = FileScanner(unstructed_files_path)
    analyzer = FileAnalyzer()
    suggester = PathSuggester(organized_files_path)
    mover = FileMover()

    print("Scanning files...")
    files = scanner.scan()
    print(f"Found {len(files)} files")

    moved_count = 0
    for file_info in files:
        analysis = analyzer.analyze(file_info)
        new_path = suggester.suggest_path(analysis)

        if new_path:
            try:
                success = mover.organize_file(analysis, new_path)
                if success:
                    print(f"{file_info['name']} -> {new_path.name}")
                    moved_count += 1
                else:
                    print(f"Failed to move {file_info['name']}")
            except Exception as e:
                print(f"Error moving {file_info['name']}: {e}")
        else:
            print(f"Skipped {file_info['name']} (already organized)")

    print(f"Organization complete! Moved {moved_count}/{len(files)} files")


if __name__ == "__main__":
    main()

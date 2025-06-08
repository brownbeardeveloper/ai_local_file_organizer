#!/usr/bin/env python3
"""AI File Organizer - Clean and simple file organization"""

from pathlib import Path
from scanner import FileScanner
from analyzer import FileAnalyzer
from openai_suggester import OpenAIPathPlanner
from mover import FileMover


def main():
    root_path = Path(".").resolve()
    unstructed_files_path = root_path / "unstructed_files"
    organized_files_path = root_path / "organized_files"

    scanner = FileScanner(unstructed_files_path)
    analyzer = FileAnalyzer()
    pathplanner = OpenAIPathPlanner()
    mover = FileMover(root_dir=str(organized_files_path), copy_mode=True)

    print("Scanning files...")
    files = scanner.scan()
    print(f"Found {len(files)} files")

    moved_count = 0
    for file_info in files:
        analysis = analyzer.analyze(file_info)
        new_path = pathplanner.suggest_paths([analysis])

        if new_path:
            try:
                final_destination = mover.organize_file(analysis, new_path)
                if final_destination:
                    final_name = Path(final_destination).name
                    print(f"{file_info['name']} -> {final_name}")
                    moved_count += 1
                else:
                    print(f"Failed to organize {file_info['name']}")
            except Exception as e:
                print(f"Error organizing {file_info['name']}: {e}")
        else:
            print(f"Skipped {file_info['name']} (already organized)")

    print(
        f"Organization complete! Organized {moved_count}/{len(files)} files (originals preserved)"
    )


if __name__ == "__main__":
    main()

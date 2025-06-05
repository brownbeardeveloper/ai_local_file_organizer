#!/usr/bin/env python3
"""AI File Organizer - Clean and simple file organization"""

from pathlib import Path
from scanner import FileScanner
from analyzer import FileAnalyzer
from suggester import PathSuggester


def main():
    # Setup
    root_path = Path(".").resolve()
    unstructed_files_path = root_path / "unstructed_files"
    organized_files_path = root_path / "organized_files"

    scanner = FileScanner(unstructed_files_path)
    analyzer = FileAnalyzer()
    suggester = PathSuggester(organized_files_path)
    # Scan files
    print("🔍 Scanning files...")
    files = scanner.scan()
    print(f"Found {len(files)} files")

    # Process each file
    for file_info in files:
        # Analyze
        analysis = analyzer.analyze(file_info)

        # Get suggestion
        new_path = suggester.suggest_path(analysis)

        if new_path:
            print(f"📁 {file_info['name']} → {new_path.name}")

    print("✅ Analysis complete")


if __name__ == "__main__":
    main()

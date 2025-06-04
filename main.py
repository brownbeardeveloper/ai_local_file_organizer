#!/usr/bin/env python3
"""AI File Organizer - Clean and simple file organization"""

from pathlib import Path
from scanner import FileScanner
from analyzer import FileAnalyzer
from suggester import PathSuggester
from mover import FileMover


def main():
    # Setup paths
    root_path = Path(".").resolve()
    data_path = root_path / "organized_files"

    # Create all instances
    scanner = FileScanner(root_path)
    analyzer = FileAnalyzer()
    suggester = PathSuggester(data_path)
    mover = FileMover()

    # Step 1: Scan for files
    print("🔍 Scanning files...")
    files_to_organize = scanner.scan()

    if not files_to_organize:
        print("No files found to organize!")
        return

    print(f"Found {len(files_to_organize)} items to analyze")

    # Step 2: Analyze each file and create move plan
    print("🧠 Analyzing files...")
    move_plan = []

    for file_info in files_to_organize:
        analysis = analyzer.analyze(file_info)
        suggested_path = suggester.suggest_path(file_info, analysis)

        if suggested_path and suggested_path != file_info["path"]:
            move_plan.append(
                {
                    "source": file_info["path"],
                    "destination": suggested_path,
                    "analysis": analysis,
                }
            )

    if not move_plan:
        print("No reorganization needed!")
        return

    # Step 3: Show plan
    print(f"\n📋 Plan: {len(move_plan)} files to organize")
    for move in move_plan[:5]:  # Show first 5
        print(f"  {move['source'].name} → {move['destination'].relative_to(root_path)}")

    if len(move_plan) > 5:
        print(f"  ... and {len(move_plan) - 5} more")

    # Step 4: Execute (dry run for now)
    print("\n✅ Dry run complete. Files would be organized as shown above.")


if __name__ == "__main__":
    main()

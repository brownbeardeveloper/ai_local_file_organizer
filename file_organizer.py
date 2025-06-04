#!/usr/bin/env python3
"""
AI-Powered File Organizer Library
Core functionality for intelligently organizing files using local LLM and computer vision
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from scanner import FileScanner
from analyzer import FileAnalyzer
from suggester import PathSuggester
from mover import FileMover


class FileOrganizer:
    """
    Main file organizer class that coordinates scanning, analysis, and moving of files.
    """

    def __init__(self, root_path: Path, data_path: Path):
        self.root_path = root_path
        self.data_path = data_path
        self.scanner = FileScanner(root_path)
        self.analyzer = FileAnalyzer()
        self.suggester = PathSuggester(data_path)
        self.mover = FileMover()

        # Create base directories
        self._create_base_structure()

    def _create_base_structure(self):
        """Create the base directory structure"""
        base_dirs = [
            self.data_path / "documents",
            self.data_path / "media" / "images",
            self.data_path / "media" / "videos",
            self.data_path / "media" / "audio",
            self.data_path / "archives",
            self.data_path / "large_files",
            self.data_path / "hidden_files",
            self.data_path / "misc",
            self.root_path / "github",
            self.root_path / "local" / "code",
        ]

        for dir_path in base_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def organize(self, dry_run: bool = True):
        """Main organization workflow"""
        print("\n🔍 Scanning files...")
        files_to_organize = self.scanner.scan()

        if not files_to_organize:
            print("No files found to organize!")
            return

        print(f"Found {len(files_to_organize)} items to analyze\n")

        # Analyze files and get suggestions
        print("🧠 Analyzing files and generating suggestions...")
        move_plan = []

        for i, file_info in enumerate(files_to_organize):
            print(f"Processing {i + 1}/{len(files_to_organize)}: {file_info['path'].name}")
            # Analyze file
            analysis = self.analyzer.analyze(file_info)
            # Get suggested path
            suggested_path = self.suggester.suggest_path(file_info, analysis)
            if suggested_path and suggested_path != file_info["path"]:
                move_plan.append(
                    {
                        "source": file_info["path"],
                        "destination": suggested_path,
                        "type": file_info["type"],
                        "analysis": analysis,
                    }
                )

        if not move_plan:
            print("No reorganization needed!")
            return

        # Display the plan
        self._display_plan(move_plan)

        # Ask for confirmation
        if not dry_run:
            if input("\nExecute this organization plan? (y/n): ").lower() == 'y':
                self._execute_plan(move_plan)
            else:
                print("Organization cancelled")
        else:
            print("\nDry run complete. Use --execute to perform the moves")

    def _display_plan(self, move_plan: List[Dict]):
        """Display the organization plan in a nice format"""
        print("\n📋 Organization Plan:\n")

        # Group by destination type
        grouped = {}
        for item in move_plan:
            dest_type = self._get_destination_type(item["destination"])
            if dest_type not in grouped:
                grouped[dest_type] = []
            grouped[dest_type].append(item)

        # Print a simple tree-like structure
        print("Organization Structure:")
        for dest_type, items in grouped.items():
            print(f"- {dest_type}:")
            for item in items[:5]:  # Show first 5 items
                source_name = item["source"].name
                dest_relative = item["destination"].relative_to(self.root_path)
                print(f"    {source_name} → {dest_relative}")
            if len(items) > 5:
                print(f"    ... and {len(items) - 5} more")

        # Summary table
        print("\nSummary:")
        print(f"{'Category':<20} {'Count':<5}")
        for dest_type, items in grouped.items():
            print(f"{dest_type:<20} {len(items):<5}")
        print(f"{'Total':<20} {len(move_plan):<5}")

    def _get_destination_type(self, path: Path) -> str:
        """Get a friendly name for the destination type"""
        path_str = str(path)
        if "github" in path_str:
            return "GitHub Projects"
        elif "local/code" in path_str:
            return "Local Code Projects"
        elif "documents" in path_str:
            return "Documents"
        elif "media/images" in path_str:
            return "Images"
        elif "media/videos" in path_str:
            return "Videos"
        elif "media/audio" in path_str:
            return "Audio"
        elif "archives" in path_str:
            return "Archives"
        elif "large_files" in path_str:
            return "Large Files"
        elif "hidden_files" in path_str:
            return "Hidden Files"
        else:
            return "Miscellaneous"

    def _execute_plan(self, move_plan: List[Dict]):
        """Execute the organization plan"""
        print("\n🚀 Executing organization plan...\n")
        success_count = 0
        error_count = 0
        for i, move in enumerate(move_plan):
            print(f"Moving {i + 1}/{len(move_plan)}: {move['source'].name}")
            try:
                self.mover.move(move["source"], move["destination"])
                success_count += 1
            except Exception as e:
                print(f"Error moving {move['source']}: {e}")
                error_count += 1
        print(f"\n✅ Successfully moved: {success_count} files")
        if error_count > 0:
            print(f"❌ Errors: {error_count} files")

#!/usr/bin/env python3
"""
AI-Powered File Organizer
Intelligently organizes files using local LLM and computer vision
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Confirm

from scanner import FileScanner
from analyzer import FileAnalyzer
from suggester import PathSuggester
from mover import FileMover

console = Console()


class FileOrganizer:
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
        console.print("\n🔍 [bold cyan]Scanning files...[/bold cyan]")
        files_to_organize = self.scanner.scan()

        if not files_to_organize:
            console.print("[yellow]No files found to organize![/yellow]")
            return

        console.print(
            f"[green]Found {len(files_to_organize)} items to analyze[/green]\n"
        )

        # Analyze files and get suggestions
        console.print(
            "🧠 [bold cyan]Analyzing files and generating suggestions...[/bold cyan]"
        )
        move_plan = []

        with console.status("[bold green]Processing files...") as status:
            for i, file_info in enumerate(files_to_organize):
                status.update(
                    f"Processing {i + 1}/{len(files_to_organize)}: {file_info['path'].name}"
                )

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
            console.print("[yellow]No reorganization needed![/yellow]")
            return

        # Display the plan
        self._display_plan(move_plan)

        # Ask for confirmation
        if not dry_run:
            if Confirm.ask("\n[bold]Execute this organization plan?[/bold]"):
                self._execute_plan(move_plan)
            else:
                console.print("[red]Organization cancelled[/red]")
        else:
            console.print(
                "\n[yellow]Dry run complete. Use --execute to perform the moves[/yellow]"
            )

    def _display_plan(self, move_plan: List[Dict]):
        """Display the organization plan in a nice format"""
        console.print("\n📋 [bold cyan]Organization Plan:[/bold cyan]\n")

        # Group by destination type
        grouped = {}
        for item in move_plan:
            dest_type = self._get_destination_type(item["destination"])
            if dest_type not in grouped:
                grouped[dest_type] = []
            grouped[dest_type].append(item)

        # Create a tree view
        tree = Tree("📁 Organization Structure")

        for dest_type, items in grouped.items():
            branch = tree.add(f"[bold]{dest_type}[/bold]")
            for item in items[:5]:  # Show first 5 items
                source_name = item["source"].name
                dest_relative = item["destination"].relative_to(self.root_path)
                branch.add(f"{source_name} → {dest_relative}")

            if len(items) > 5:
                branch.add(f"[dim]... and {len(items) - 5} more[/dim]")

        console.print(tree)

        # Summary table
        table = Table(title="\n📊 Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")

        for dest_type, items in grouped.items():
            table.add_row(dest_type, str(len(items)))

        table.add_row("[bold]Total[/bold]", f"[bold]{len(move_plan)}[/bold]")
        console.print(table)

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
        console.print("\n🚀 [bold cyan]Executing organization plan...[/bold cyan]")

        success_count = 0
        error_count = 0

        with console.status("[bold green]Moving files...") as status:
            for i, move in enumerate(move_plan):
                status.update(f"Moving {i + 1}/{len(move_plan)}: {move['source'].name}")

                try:
                    self.mover.move(move["source"], move["destination"])
                    success_count += 1
                except Exception as e:
                    console.print(f"[red]Error moving {move['source']}: {e}[/red]")
                    error_count += 1

        console.print(f"\n[green]✅ Successfully moved: {success_count} files[/green]")
        if error_count > 0:
            console.print(f"[red]❌ Errors: {error_count} files[/red]")


@click.command()
@click.option("--path", "-p", default=".", help="Path to organize")
@click.option(
    "--execute", "-e", is_flag=True, help="Execute the moves (default is dry-run)"
)
@click.option("--data-dir", "-d", default="files", help="Directory for organized files")
def main(path, execute, data_dir):
    """AI-Powered File Organizer - Intelligently organize your files"""
    console.print("[bold cyan]🤖 AI File Organizer[/bold cyan]")
    console.print("[dim]Using Ollama and ResNet for intelligent organization[/dim]\n")

    root_path = Path(path).resolve()
    data_path = root_path / data_dir

    organizer = FileOrganizer(root_path, data_path)
    organizer.organize(dry_run=not execute)


if __name__ == "__main__":
    main()

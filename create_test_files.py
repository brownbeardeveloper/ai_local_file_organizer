#!/usr/bin/env python3
"""
Create test files for the AI File Organizer
This creates various file types to test the organization capabilities
"""

import os
from pathlib import Path
import random
import datetime


def create_test_environment():
    """Create test files and folders"""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)

    print("Creating test environment...")

    # Create some loose files
    (test_dir / "report_2023.pdf").touch()
    (test_dir / "vacation_photo.jpg").touch()
    (test_dir / "meeting_notes.txt").write_text(
        "Important meeting notes from last week..."
    )
    (test_dir / ".hidden_config").write_text("secret=12345")
    (test_dir / "large_video.mp4").write_text("x" * (101 * 1024 * 1024))  # 101MB file
    (test_dir / "data.csv").write_text("name,age\nJohn,25\nJane,30")
    (test_dir / "backup_2023.zip").touch()

    # Create a Python project with git
    py_project = test_dir / "my_python_app"
    py_project.mkdir(exist_ok=True)
    (py_project / ".git").mkdir(exist_ok=True)
    (py_project / "requirements.txt").write_text("flask==2.0.0\nrequests==2.28.0")
    (py_project / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
    (py_project / ".env").write_text("DATABASE_URL=postgres://localhost/mydb")

    # Create a Next.js project without git
    next_project = test_dir / "nextjs_website"
    next_project.mkdir(exist_ok=True)
    (next_project / "package.json").write_text('{"name": "my-app", "dependencies": {}}')
    (next_project / "next.config.js").write_text("module.exports = {}")
    (next_project / "pages").mkdir(exist_ok=True)
    (next_project / "pages" / "index.js").write_text(
        "export default function Home() {}"
    )

    # Create some nested folders with files
    docs_folder = test_dir / "old_documents"
    docs_folder.mkdir(exist_ok=True)
    (docs_folder / "invoice_2022.pdf").touch()
    (docs_folder / "contract.docx").touch()

    # Create hidden files outside projects
    (test_dir / ".DS_Store").touch()
    (test_dir / ".bash_history").write_text("cd /\nls -la")

    print(f"✅ Test environment created in '{test_dir}'")
    print("\nTest with:")
    print(f"  python file_organizer.py --path {test_dir}")
    print(f"  python file_organizer.py --path {test_dir} --execute")


if __name__ == "__main__":
    create_test_environment()

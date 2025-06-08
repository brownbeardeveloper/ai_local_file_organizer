# 🤖 AI File Organizer

**Stop wasting hours organizing files manually.** Let AI do it in seconds.

```bash
python main.py
# ✨ 247 files organized in 12 seconds
# 📁 Documents → organized_files/work/reports/
# 🖼️ Screenshots → organized_files/personal/images/
# 📊 Spreadsheets → organized_files/finance/data/
```

## 🚀 What It Does

- **Scans** your messy directories
- **Analyzes** file content with AI (OpenAI GPT)
- **Suggests** intelligent folder structures
- **Organizes** everything automatically

Perfect for developers drowning in downloads, documents, and random files.

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd ai_file_organization
pip install -r requirements.txt

# 2. Add your OpenAI API key
export OPENAI_API_KEY="your-key-here"

# 3. Run it
python main.py
```

**That's it.** Your files go from chaos to organized in under a minute.

## 📁 Before vs After

```
BEFORE:
├── random_stuff/
│   ├── IMG_2394.jpg
│   ├── budget_2024.xlsx
│   ├── meeting_notes.pdf
│   └── screenshot_001.png

AFTER:
├── organized_files/
│   ├── personal/
│   │   └── photos/IMG_2394.jpg
│   ├── finance/
│   │   └── spreadsheets/budget_2024.xlsx
│   ├── work/
│   │   └── documents/meeting_notes.pdf
│   └── screenshots/screenshot_001.png
```

## 🛠️ Configuration

```python
# Customize source and destination
organizer = create_organizer(
    source_dir=Path("./my_messy_folder"),
    target_dir=Path("./clean_organized"),
    copy_mode=True  # Keep originals safe
)
```

## 🏗️ Architecture

Built with clean, fail-fast Python following enterprise patterns:

- **FileScanner**: Discovers files to organize
- **FileAnalyzer**: AI-powered content analysis  
- **OpenAIPathPlanner**: Generates smart folder structures
- **FileMover**: Safely moves/copies files
- **FileOrganizer**: Orchestrates the entire workflow

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Basic file system permissions

## 🎯 Perfect For

- **Developers** with cluttered Downloads folders
- **Content creators** managing thousands of assets
- **Anyone** tired of manual file organization

## 🔧 Advanced Usage

### 🧠 Better AI Analysis
For improved file analysis accuracy, use a stronger Qwen model:

```python
# Enhanced file analysis with stronger AI models
from analyzer import FileAnalyzer

# Use stronger Qwen model for better content understanding
analyzer = FileAnalyzer(model="qwen3:32b")  # Use this or stronger models for better results
```

---

**Made by developers, for developers.** Because life's too short to organize files manually. 
# 🤖 AI File Organizer Version 1.1

**Stop wasting hours organizing files manually.** Let AI do it in seconds.

## 🎯 Perfect For

- **Developers** drowning in Downloads folders and random project files
- **Content creators** managing thousands of photos, videos, and documents
- **Professionals** with messy desktop and document chaos
- **Anyone** tired of spending hours organizing files manually

## 🚀 What It Does

Transform your digital chaos into organized perfection:

1. **🔍 Scans** your messy directories intelligently
2. **🧠 Analyzes** file content using advanced AI models
3. **📋 Suggests** smart folder structures based on content
4. **📁 Organizes** everything automatically while keeping originals safe

The AI actually *understands* your files - reading documents, recognizing objects in photos, analyzing code purpose, and creating logical folder structures that make sense.

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

## 📁 The Transformation

See the magic in action:

```
BEFORE: Digital Chaos
├── random_stuff/
│   ├── IMG_2394.jpg          # Vacation photo
│   ├── budget_2024.xlsx      # Financial spreadsheet  
│   ├── meeting_notes.pdf     # Work document
│   ├── screenshot_001.png    # UI mockup
│   └── backup_script.py      # Automation script

AFTER: Intelligent Organization  
├── organized_files/
│   ├── personal/
│   │   └── photos/IMG_2394.jpg
│   ├── finance/
│   │   └── spreadsheets/budget_2024.xlsx
│   ├── work/
│   │   └── documents/meeting_notes.pdf
│   ├── screenshots/
│   │   └── ui_mockups/screenshot_001.png
│   └── development/
│       └── scripts/backup_script.py
```

## 📋 What Files It Handles

### ✅ **Full AI Analysis & Organization**

**🖼️ Images** - *Smart object recognition*
- **Formats:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff` + RAW formats (`.arw`, `.cr2`, `.nef`, etc.)
- **Intelligence:** Recognizes objects, extracts photo dates, classifies by content and age

**📄 Documents** - *Content understanding*
- **Text:** `.txt`, `.md` → Analyzes topics and content themes
- **PDFs:** `.pdf` → Extracts text, OCR for scanned docs, understands document purpose  
- **Office:** `.doc`, `.docx` → Analyzes structure and content sampling
- **Data:** `.csv` → Detects data types, identifies business context
- **Code:** `.py`, `.js`, `.sh`, `.html`, `.css` → Understands script purpose and functionality

### ⚠️ **Basic Organization** *(Enhanced analysis coming soon)*

**🎵 Audio:** `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg` → Detected and categorized

**🎬 Video:** `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv` → Detected and categorized  

**🗜️ Archives:** `.zip`, `.rar`, `.tar`, `.gz`, `.7z` → Basic categorization

### 🚫 **Smart Exclusions**

The AI intelligently avoids organizing:
- **System files** (`.DS_Store`, cache files, logs)
- **Project directories** (recognizes `package.json`, `.git`, etc.)
- **Build artifacts** (`node_modules`, `dist`, `__pycache__`)

*This prevents accidentally moving your development workspace!*

## 🛠️ Customization

```python
# Organize specific directories
organizer = create_organizer(
    source_dir=Path("./Downloads"),        # What to organize
    target_dir=Path("./Organized"),        # Where to put it
    copy_mode=True                         # Keep originals safe
)

# Advanced AI configuration
analyzer = FileAnalyzer(
    large_file_threshold_mb=50,            # Skip huge files
    yolo_analyzer=YOLOAnalyzer(),          # Image recognition
    ollama_analyzer=OllamaAnalyzer()       # Text analysis
)
```

## 🏗️ Technical Architecture

Enterprise-grade Python following clean architecture principles:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   FileScanner   │───▶│   FileAnalyzer   │───▶│  OpenAIPathPlanner  │
│ Discovers files │    │ AI content analysis│    │ Generates structure │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                │                           │
                                ▼                           ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   FileMover     │◀───│ FileOrganizer    │◀───│     Results         │
│ Safe operations │    │ Orchestrates all │    │  Smart organization │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

**AI Models Used:**
- **YOLO11n** for image object detection (80 classes)
- **Qwen 1.7B** for document content analysis  
- **PaddleOCR** for text extraction from images/PDFs
- **OpenAI GPT** for intelligent path planning

## ⚠️ Current Limitations & Roadmap

### **Performance Constraints**

**🧠 Model Limitations**
- Using Qwen 1.7B (hardware optimized) - 8B+ models would significantly improve accuracy
- YOLO11n limited to 80 object classes for image recognition
- Large files (>100MB) skipped for memory efficiency

**📱 Media Analysis Gap**  
- Music files: No genre/artist extraction yet
- Video files: No scene/content analysis yet

### **🚀 Immediate Improvements**

**Q1 2024 Roadmap:**
- **OpenAI Integration** → GPT-4.1-mini for superior analysis (~8B parameters)
- **Media Intelligence** → Music genre detection, video scene analysis
- **Project Awareness** → README-based analysis for code repositories

**Future Vision:**
- Custom model fine-tuning for specialized domains
- Multi-modal analysis (text + image + audio combined)
- Expanded visual recognition beyond current 80 classes

*Building within hardware constraints while maintaining professional-grade quality.*

## 📋 Requirements

- **Python 3.8+**
- **OpenAI API key** (for path planning)
- **8GB+ RAM recommended** (for AI models)
- **Basic file permissions**

## 🚀 Installation & Setup

```bash
# Quick setup
git clone <repo-url>
cd ai_file_organization
pip install -r requirements.txt

# Configure OpenAI
export OPENAI_API_KEY="your-api-key"

# Optional: Better models (if you have more RAM)
# Use qwen3:8b for improved analysis accuracy
```

---

**Built by developers, for developers.** Because intelligent automation beats manual labor every time. 
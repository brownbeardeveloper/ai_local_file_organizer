"""
File Analyzer Module
Orchestrates file content analysis using specialized AI model analyzers
"""

from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import exifread
from PIL import Image
from yolo_analyzer import YOLOAnalyzer
from ollama_analyzer import OllamaAnalyzer


class FileAnalyzer:
    """Orchestrates file analysis using specialized AI analyzers"""

    def __init__(
        self,
        large_file_threshold: int = 100 * 1024 * 1024,
        yolo_analyzer: Optional[YOLOAnalyzer] = None,
        ollama_analyzer: Optional[OllamaAnalyzer] = None,
        # Backward compatibility - create default analyzers if not provided
        yolo_model_name: str = "yolo11n.pt",
        ollama_model_name: str = "mistral:latest",
    ):
        self.large_file_threshold = large_file_threshold

        # Use provided analyzers or create default ones
        self.yolo_analyzer = yolo_analyzer or YOLOAnalyzer(yolo_model_name)
        self.ollama_analyzer = ollama_analyzer or OllamaAnalyzer(ollama_model_name)

    def analyze(self, file_info: Dict) -> Dict[str, Any]:
        """Analyze file content and return insights about what's inside"""
        file_path = Path(file_info["path"])

        # Start with file metadata from scanner and add analysis results
        analysis = {
            # Preserve original file metadata
            "path": file_info["path"],
            "name": file_info["name"],
            "suffix": file_info["suffix"],
            "category": file_info["category"],
            "size": file_info["size"],
            "modified": file_info["modified"],
            "mime_type": file_info["mime_type"],
            # Analysis results
            "content_analysis": "pending",
            "ai_insights": {},
        }

        # Content analysis based on file category from scanner
        file_category = file_info.get("category", "other")

        if file_category == "image":
            analysis.update(self._analyze_image_content(file_path))
        elif file_category == "document":
            analysis.update(self._analyze_document_content(file_path, file_info))
        elif file_category == "video":
            analysis.update(self._analyze_video_content(file_path))
        elif file_category == "audio":
            analysis.update(self._analyze_audio_content(file_path))
        else:
            analysis["content_analysis"] = "unsupported_type"

        return analysis

    def _analyze_image_content(self, path: Path) -> Dict[str, Any]:
        """Analyze what's actually IN the image"""
        result = {
            "content_analysis": "image_analyzed",
            "ai_insights": {},
        }

        try:
            # Get image metadata first
            image = Image.open(path).convert("RGB")
            width, height = image.size
            aspect_ratio = width / height

            # Determine image characteristics
            if aspect_ratio > 1.5:
                image_type = "panoramic"
            elif abs(aspect_ratio - 1.0) < 0.1:
                image_type = "square"
            elif width < 800 or height < 600:
                image_type = "small_image"
            elif width > 3000 or height > 3000:
                image_type = "high_resolution"
            else:
                image_type = "standard"

            result["ai_insights"]["image_type"] = image_type
            result["ai_insights"]["dimensions"] = f"{width}x{height}"

            # YOLO analysis for object detection
            if self.yolo_analyzer.is_available():
                detected_objects = self.yolo_analyzer.detect_objects(image)
                if detected_objects:
                    result["ai_insights"].update(detected_objects)

            # Extract EXIF for photo metadata
            self._extract_photo_context(path, result)

        except Exception as e:
            result["content_analysis"] = f"image_error: {str(e)}"

        return result

    def _analyze_document_content(self, path: Path, file_info: Dict) -> Dict[str, Any]:
        """Analyze what's actually IN the document"""
        result = {
            "content_analysis": "document_analyzed",
            "ai_insights": {},
        }

        try:
            suffix = file_info.get("suffix", "").lower()
            file_size = file_info.get("size", 0)

            # Skip empty files
            if file_size == 0:
                result["ai_insights"]["content"] = "empty_file"
                return result

            # Skip very large files (>5MB) for content analysis
            if file_size > 5 * 1024 * 1024:
                result["ai_insights"]["content"] = "large_file_skipped"
                return result

            if suffix == ".pdf":
                content_info = self._analyze_pdf_content(path)
            elif suffix in [".txt", ".md"]:
                content_info = self._analyze_text_content(path)
            elif suffix in [".doc", ".docx"]:
                content_info = self._analyze_word_content(path)
            elif suffix in [".csv"]:
                content_info = self._analyze_csv_content(path)
            elif suffix in [".py", ".js", ".sh", ".html", ".css"]:
                content_info = self._analyze_code_content(path)
            else:
                content_info = {"content": "unsupported_document_type"}

            result["ai_insights"].update(content_info)

        except Exception as e:
            result["content_analysis"] = f"document_error: {str(e)}"

        return result

    def _analyze_video_content(self, path: Path) -> Dict[str, Any]:
        """Analyze video file characteristics"""
        return {
            "content_analysis": "video_detected",
            "ai_insights": {"content": "video_analysis_not_implemented"},
        }

    def _analyze_audio_content(self, path: Path) -> Dict[str, Any]:
        """Analyze audio file characteristics"""
        return {
            "content_analysis": "audio_detected",
            "ai_insights": {"content": "audio_analysis_not_implemented"},
        }

    def _extract_photo_context(self, path: Path, result: Dict):
        """Extract photo metadata for context"""
        try:
            with open(path, "rb") as f:
                tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
                if "EXIF DateTimeOriginal" in tags:
                    date_str = str(tags["EXIF DateTimeOriginal"])
                    try:
                        photo_date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        result["ai_insights"]["photo_date"] = photo_date.strftime(
                            "%Y-%m-%d"
                        )

                        # Determine if it's recent or old
                        days_old = (datetime.now() - photo_date).days
                        if days_old < 30:
                            result["ai_insights"]["age"] = "recent"
                        elif days_old < 365:
                            result["ai_insights"]["age"] = "this_year"
                        else:
                            result["ai_insights"]["age"] = "old"
                    except ValueError:
                        pass
        except Exception:
            pass

    def _analyze_pdf_content(self, path: Path) -> Dict[str, Any]:
        """Analyze PDF content"""
        try:
            import PyPDF2

            with open(path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                info = {
                    "pages": len(pdf_reader.pages),
                    "encrypted": pdf_reader.is_encrypted,
                }

                # Try to extract some text for content analysis
                if len(pdf_reader.pages) > 0 and not pdf_reader.is_encrypted:
                    first_page = pdf_reader.pages[0].extract_text()
                    if len(first_page) > 100:
                        # Use Ollama to analyze PDF content
                        if self.ollama_analyzer.is_available():
                            content_analysis = self.ollama_analyzer.analyze_text(
                                first_page[:1000], "document"
                            )
                            info.update(content_analysis)
                    else:
                        info["content"] = "image_based_pdf"

                return info
        except:
            return {"content": "pdf_analysis_failed"}

    def _analyze_text_content(self, path: Path) -> Dict[str, Any]:
        """Analyze text file content"""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read(2000)  # Read first 2000 chars

                if len(content.strip()) == 0:
                    return {"content": "empty_text_file"}

                # Basic content analysis
                lines = content.split("\n")
                info = {
                    "length": "short"
                    if len(content) < 500
                    else "medium"
                    if len(content) < 5000
                    else "long",
                    "lines": len(lines),
                }

                # AI content analysis
                if self.ollama_analyzer.is_available() and len(content.strip()) > 50:
                    ai_analysis = self.ollama_analyzer.analyze_text(content, "document")
                    info.update(ai_analysis)

                return info
        except:
            return {"content": "text_analysis_failed"}

    def _analyze_csv_content(self, path: Path) -> Dict[str, Any]:
        """Analyze CSV file structure"""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                first_lines = [file.readline().strip() for _ in range(3)]

            if first_lines[0]:
                columns = len(first_lines[0].split(","))
                return {
                    "content": "csv_data",
                    "columns": columns,
                    "has_header": "," in first_lines[0],
                }
            else:
                return {"content": "empty_csv"}
        except:
            return {"content": "csv_analysis_failed"}

    def _analyze_code_content(self, path: Path) -> Dict[str, Any]:
        """Analyze code file content"""
        suffix = path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".sh": "shell_script",
            ".html": "html",
            ".css": "css",
        }

        return {
            "content": "code",
            "language": language_map.get(suffix, "unknown"),
            "type": "script" if suffix == ".sh" else "source_code",
        }

    def _analyze_word_content(self, path: Path) -> Dict[str, Any]:
        """Analyze Word document content"""
        try:
            from docx import Document

            doc = Document(path)

            # Count content
            paragraph_count = len(doc.paragraphs)
            word_count = sum(
                len(p.text.split()) for p in doc.paragraphs if p.text.strip()
            )

            info = {
                "content": "word_document",
                "paragraphs": paragraph_count,
                "words": word_count,
            }

            # Get a sample of text for AI analysis
            if self.ollama_analyzer.is_available() and word_count > 0:
                sample_text = ""
                for p in doc.paragraphs[:5]:  # First 5 paragraphs
                    if p.text.strip():
                        sample_text += p.text + " "

                if len(sample_text) > 100:
                    ai_analysis = self.ollama_analyzer.analyze_text(
                        sample_text[:1000], "document"
                    )
                    info.update(ai_analysis)

            return info
        except:
            return {"content": "word_analysis_failed"}

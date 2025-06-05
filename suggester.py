"""
AI-Powered Semantic File Organization System
Intelligently organizes files based on content, context, and AI insights
"""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import re


class PathSuggester:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.root_path = data_path.parent

    def suggest_path(self, file_analysis: Dict) -> Optional[Path]:
        """Suggest optimal organization path based on AI content analysis"""
        # Don't move files that are already organized
        if self._is_already_organized(Path(file_analysis["path"])):
            return None

        # Handle different content categories intelligently
        category = file_analysis.get("category")

        if file_analysis.get("is_project"):
            return self._suggest_project_path(file_analysis)
        elif self._is_large_file(file_analysis):
            return self._suggest_large_file_path(file_analysis)
        elif category == "image":
            return self._suggest_smart_image_path(file_analysis)
        elif category == "document":
            return self._suggest_smart_document_path(file_analysis)
        elif category == "video":
            return self._suggest_smart_media_path(file_analysis, "video")
        elif category == "audio":
            return self._suggest_smart_media_path(file_analysis, "audio")
        elif category == "archive":
            return self._suggest_archive_path(file_analysis)
        else:
            return self._suggest_smart_misc_path(file_analysis)

    def _is_already_organized(self, path: Path) -> bool:
        """Check if file is already in an organized location"""
        organized_indicators = {
            "photography",
            "work",
            "personal",
            "creative",
            "development",
            "reference",
            "archive",
            "system",
            "temp",
            "organized_files",
        }
        return any(part in organized_indicators for part in path.parts)

    def _is_large_file(self, file_analysis: Dict) -> bool:
        """Determine if file should be treated as large file"""
        size = file_analysis.get("size", 0)
        return size > 100 * 1024 * 1024  # 100MB threshold

    def _suggest_smart_image_path(self, file_analysis: Dict) -> Path:
        """AI-powered intelligent image organization"""
        ai_insights = file_analysis.get("ai_insights", {})
        date = self._extract_date(file_analysis)
        year = date.year
        month = f"{date.month:02d}"

        # Get AI-detected content for smart categorization
        primary_object = ai_insights.get("primary_object", "")

        # Determine semantic category based on AI insights
        base_path = self.data_path / "photography"

        # Smart categorization based on detected content
        if self._is_screenshot_content(ai_insights, file_analysis["name"]):
            category_path = base_path / "screenshots" / "applications" / str(year)
            filename = self._generate_smart_filename(file_analysis, "screenshot")

        elif self._is_personal_photo(ai_insights):
            if primary_object in ["person", "people", "face"]:
                category_path = base_path / "personal" / "people" / str(year) / month
            elif primary_object in ["food", "meal", "restaurant"]:
                category_path = base_path / "personal" / "food" / str(year) / month
            elif primary_object in ["car", "vehicle", "motorcycle"]:
                category_path = base_path / "personal" / "vehicles" / str(year)
            else:
                category_path = base_path / "personal" / "life" / str(year) / month
            filename = self._generate_smart_filename(file_analysis, primary_object)

        elif self._is_travel_photo(ai_insights):
            category_path = base_path / "personal" / "travel" / str(year) / month
            filename = self._generate_smart_filename(
                file_analysis, primary_object or "travel"
            )

        elif self._is_work_related(ai_insights, file_analysis["name"]):
            category_path = base_path / "work" / "documentation" / str(year)
            filename = self._generate_smart_filename(file_analysis, "work-doc")

        elif primary_object in ["meme", "funny", "joke"] or self._is_meme(
            file_analysis["name"]
        ):
            category_path = base_path / "collection" / "memes"
            filename = self._generate_smart_filename(file_analysis, "meme")

        else:
            # General categorization by detected object
            if primary_object:
                object_category = self._categorize_object(primary_object)
                category_path = base_path / "general" / object_category / str(year)
                filename = self._generate_smart_filename(file_analysis, primary_object)
            else:
                category_path = (
                    base_path / "general" / "uncategorized" / str(year) / month
                )
                filename = file_analysis["name"]

        return category_path / filename

    def _suggest_smart_document_path(self, file_analysis: Dict) -> Path:
        """AI-powered intelligent document organization"""
        ai_insights = file_analysis.get("ai_insights", {})
        date = self._extract_date(file_analysis)
        year = str(date.year)

        # Analyze document content for smart categorization
        content_type = ai_insights.get("content", "")
        language = ai_insights.get("language", "")

        base_path = self.data_path / "documents"

        # Specific document types first
        if "resume" in content_type or "cv" in file_analysis["name"].lower():
            category_path = base_path / "personal" / "career" / year
        elif "insurance" in content_type:
            category_path = base_path / "personal" / "insurance" / year
        elif "certificate" in content_type:
            category_path = base_path / "personal" / "certificates" / year
        elif "notes" in content_type and "summary" in file_analysis["name"].lower():
            category_path = base_path / "reference" / "summaries"

        # Work documents
        elif self._is_work_document(ai_insights, file_analysis["name"]):
            if "report" in content_type or "analysis" in content_type:
                category_path = base_path / "work" / "reports" / year
            elif "presentation" in content_type:
                category_path = base_path / "work" / "presentations" / year
            elif "meeting" in content_type or "notes" in content_type:
                category_path = base_path / "work" / "meetings" / year
            else:
                category_path = base_path / "work" / "general" / year

        # Personal documents
        elif self._is_personal_document(ai_insights, file_analysis["name"]):
            if (
                "finance" in content_type
                or "tax" in content_type
                or "receipt" in content_type
            ):
                category_path = base_path / "personal" / "finance" / year
            elif "health" in content_type or "medical" in content_type:
                category_path = base_path / "personal" / "health" / year
            elif "legal" in content_type or "contract" in content_type:
                category_path = base_path / "personal" / "legal" / year
            else:
                category_path = base_path / "personal" / "general" / year

        # Reference materials
        elif self._is_reference_document(ai_insights, file_analysis["name"]):
            if "manual" in content_type or "guide" in content_type:
                category_path = base_path / "reference" / "manuals"
            elif language and language != "unknown":
                category_path = base_path / "reference" / "code" / language
            else:
                category_path = base_path / "reference" / "general"

        else:
            # Default categorization
            category_path = base_path / "general" / year

        filename = self._generate_smart_filename(
            file_analysis, content_type or "document"
        )
        return category_path / filename

    def _suggest_project_path(self, file_analysis: Dict) -> Path:
        """Organize project directories intelligently"""
        project_name = Path(file_analysis["path"]).name

        # Simple project categorization
        if self._is_development_project(project_name):
            return self.data_path / "development" / project_name
        else:
            return self.data_path / "projects" / project_name

    def _suggest_smart_media_path(self, file_analysis: Dict, media_type: str) -> Path:
        """Smart media file organization"""
        ai_insights = file_analysis.get("ai_insights", {})
        date = self._extract_date(file_analysis)
        year = str(date.year)

        base_path = self.data_path / "media" / media_type

        # Categorize by content if available
        if media_type == "video":
            if self._is_personal_video(ai_insights, file_analysis["name"]):
                category_path = base_path / "personal" / year
            elif self._is_work_video(ai_insights, file_analysis["name"]):
                category_path = base_path / "work" / "recordings" / year
            else:
                category_path = base_path / "general" / year
        else:  # audio
            category_path = base_path / "general" / year

        filename = self._generate_smart_filename(file_analysis, media_type)
        return category_path / filename

    def _suggest_large_file_path(self, file_analysis: Dict) -> Path:
        """Organize large files by category and importance"""
        category = file_analysis.get("category", "misc")
        date = self._extract_date(file_analysis)
        year = str(date.year)

        base_path = self.data_path / "archive" / "large-files"
        category_path = base_path / category / year

        filename = self._generate_smart_filename(file_analysis, "large-file")
        return category_path / filename

    def _suggest_archive_path(self, file_analysis: Dict) -> Path:
        """Smart archive organization"""
        date = self._extract_date(file_analysis)
        year = str(date.year)

        filename = self._generate_smart_filename(file_analysis, "archive")
        return self.data_path / "archive" / "compressed" / year / filename

    def _suggest_smart_misc_path(self, file_analysis: Dict) -> Path:
        """Smart miscellaneous file organization"""
        suffix = file_analysis.get("suffix", "").lower()
        date = self._extract_date(file_analysis)
        year = str(date.year)

        if suffix:
            ext_category = suffix[1:]  # Remove dot
            category_path = self.data_path / "system" / "by-type" / ext_category / year
        else:
            category_path = self.data_path / "system" / "no-extension" / year

        filename = self._generate_smart_filename(file_analysis, "misc")
        return category_path / filename

    # Helper methods for intelligent categorization
    def _extract_date(self, file_analysis: Dict) -> datetime:
        """Extract the most relevant date for organization"""
        ai_insights = file_analysis.get("ai_insights", {})

        # Try AI-detected photo date first
        if "photo_date" in ai_insights:
            try:
                return datetime.strptime(ai_insights["photo_date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        # Fall back to file modification date
        try:
            return datetime.strptime(file_analysis["modified"], "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime.now()

    def _generate_smart_filename(self, file_analysis: Dict, content_hint: str) -> str:
        """Generate intelligent filename based on content and AI insights"""
        ai_insights = file_analysis.get("ai_insights", {})
        original_name = file_analysis["name"]
        suffix = file_analysis.get("suffix", "")

        # Use primary object if available
        primary_object = ai_insights.get("primary_object", "")
        if primary_object and primary_object != "object":
            base_name = self._clean_filename(primary_object)
        elif content_hint and content_hint not in ["misc", "document", "large-file"]:
            base_name = self._clean_filename(content_hint)
        else:
            # Keep original name but clean it
            base_name = self._clean_filename(original_name.replace(suffix, ""))

            # Add more specific content details if available
        if ai_insights.get("content") and ai_insights["content"] not in [
            "unknown",
            "misc",
        ]:
            content_detail = self._clean_filename(ai_insights["content"])
            if content_detail and content_detail != base_name:
                base_name = content_detail

        # Add confidence or other context if high-confidence detection
        confidence = ai_insights.get("confidence", "")
        if confidence and "%" in confidence:
            try:
                conf_num = float(confidence.replace("%", ""))
                if conf_num >= 90:
                    base_name += "-hq"  # High quality detection
            except ValueError:
                pass  # Skip if confidence format is unexpected

        return f"{base_name}{suffix}"

    def _clean_filename(self, name: str) -> str:
        """Clean filename for filesystem compatibility"""
        # Replace spaces and special chars with hyphens
        cleaned = re.sub(r"[^\w\-_.]", "-", name.lower())
        # Remove multiple consecutive hyphens
        cleaned = re.sub(r"-+", "-", cleaned)
        # Remove leading/trailing hyphens
        return cleaned.strip("-")

    def _categorize_object(self, obj: str) -> str:
        """Map detected objects to logical categories"""
        obj = obj.lower()

        # People and faces
        if obj in ["person", "people", "face", "child", "man", "woman"]:
            return "people"

        # Food and dining
        if obj in [
            "food",
            "meal",
            "pizza",
            "sandwich",
            "cake",
            "fruit",
            "dining-table",
            "dining table",
            "table",
        ]:
            return "food"

        # Animals
        if obj in ["cat", "dog", "bird", "horse", "cow", "sheep", "animal"]:
            return "animals"

        # Vehicles
        if obj in ["car", "truck", "bus", "motorcycle", "bicycle", "plane", "boat"]:
            return "vehicles"

        # Objects and items
        if obj in [
            "chair",
            "sofa",
            "bed",
            "tv",
            "laptop",
            "phone",
            "book",
            "bottle",
            "cup",
            "clock",
            "scissors",
            "teddy bear",
            "hair drier",
            "toothbrush",
        ]:
            return "objects"

        # Default fallback
        return "objects"

    # Content detection helpers
    def _is_screenshot_content(self, ai_insights: Dict, filename: str) -> bool:
        """Detect if image is a screenshot"""
        filename_lower = filename.lower()
        screenshot_indicators = ["screenshot", "screen shot", "capture", "grab"]
        return (
            any(indicator in filename_lower for indicator in screenshot_indicators)
            or ai_insights.get("image_type") == "screenshot"
        )

    def _is_personal_photo(self, ai_insights: Dict) -> bool:
        """Detect personal photos vs professional/work photos"""
        personal_objects = {"person", "people", "family", "food", "pet", "home"}
        primary_object = ai_insights.get("primary_object", "").lower()
        return primary_object in personal_objects

    def _is_travel_photo(self, ai_insights: Dict) -> bool:
        """Detect travel photos"""
        travel_objects = {
            "landmark",
            "monument",
            "building",
            "landscape",
            "beach",
            "mountain",
        }
        primary_object = ai_insights.get("primary_object", "").lower()
        return primary_object in travel_objects

    def _is_work_related(self, ai_insights: Dict, filename: str) -> bool:
        """Detect work-related content"""
        work_indicators = [
            "meeting",
            "presentation",
            "report",
            "work",
            "office",
            "business",
        ]
        filename_lower = filename.lower()
        return any(indicator in filename_lower for indicator in work_indicators)

    def _is_meme(self, filename: str) -> bool:
        """Detect meme files"""
        meme_indicators = ["meme", "funny", "lol", "joke", "humor"]
        filename_lower = filename.lower()
        return any(indicator in filename_lower for indicator in meme_indicators)

    def _is_work_document(self, ai_insights: Dict, filename: str) -> bool:
        """Detect work documents"""
        work_indicators = [
            "report",
            "meeting",
            "presentation",
            "analysis",
            "business",
            "work",
        ]
        content = ai_insights.get("content", "").lower()
        filename_lower = filename.lower()
        return any(indicator in content for indicator in work_indicators) or any(
            indicator in filename_lower for indicator in work_indicators
        )

    def _is_personal_document(self, ai_insights: Dict, filename: str) -> bool:
        """Detect personal documents"""
        personal_indicators = [
            "tax",
            "receipt",
            "bank",
            "finance",
            "personal",
            "health",
            "medical",
        ]
        content = ai_insights.get("content", "").lower()
        filename_lower = filename.lower()
        return any(indicator in content for indicator in personal_indicators) or any(
            indicator in filename_lower for indicator in personal_indicators
        )

    def _is_reference_document(self, ai_insights: Dict, filename: str) -> bool:
        """Detect reference materials"""
        reference_indicators = [
            "manual",
            "guide",
            "documentation",
            "reference",
            "howto",
        ]
        content = ai_insights.get("content", "").lower()
        filename_lower = filename.lower()
        return any(indicator in content for indicator in reference_indicators) or any(
            indicator in filename_lower for indicator in reference_indicators
        )

    def _is_development_project(self, project_name: str) -> bool:
        """Detect development projects"""
        dev_indicators = [
            "web",
            "app",
            "react",
            "vue",
            "angular",
            "python",
            "js",
            "node",
            "mobile",
            "ios",
            "android",
            "flutter",
            "data",
            "ml",
            "ai",
            "api",
        ]
        name_lower = project_name.lower()
        return any(indicator in name_lower for indicator in dev_indicators)

    def _is_personal_video(self, ai_insights: Dict, filename: str) -> bool:
        """Detect personal videos"""
        personal_indicators = ["family", "vacation", "personal", "home"]
        filename_lower = filename.lower()
        return any(indicator in filename_lower for indicator in personal_indicators)

    def _is_work_video(self, ai_insights: Dict, filename: str) -> bool:
        """Detect work videos"""
        work_indicators = ["meeting", "presentation", "training", "work", "conference"]
        filename_lower = filename.lower()
        return any(indicator in filename_lower for indicator in work_indicators)

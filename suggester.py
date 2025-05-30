"""
Path Suggester Module
Suggests optimal organization paths based on file analysis
"""

from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class PathSuggester:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.root_path = data_path.parent

    def suggest_path(self, file_info: Dict, analysis: Dict) -> Optional[Path]:
        """Suggest a new path for the file based on analysis"""
        # Don't move files that are already organized
        if self._is_already_organized(file_info["path"]):
            return None

        # Handle different file types
        if file_info.get("is_project"):
            return self._suggest_project_path(file_info, analysis)
        elif analysis.get("is_large"):
            return self._suggest_large_file_path(file_info, analysis)
        elif analysis.get("category") == "hidden":
            return self._suggest_hidden_file_path(file_info)
        elif analysis.get("category") == "image":
            return self._suggest_image_path(file_info, analysis)
        elif analysis.get("category") == "document":
            return self._suggest_document_path(file_info, analysis)
        elif analysis.get("category") == "video":
            return self._suggest_media_path(file_info, "videos")
        elif analysis.get("category") == "audio":
            return self._suggest_media_path(file_info, "audio")
        elif analysis.get("category") == "archive":
            return self._suggest_archive_path(file_info)
        else:
            return self._suggest_misc_path(file_info, analysis)

    def _is_already_organized(self, path: Path) -> bool:
        """Check if file is already in an organized location"""
        path_str = str(path)
        organized_paths = ["files/", "github/", "local/code/"]
        return any(org_path in path_str for org_path in organized_paths)

    def _suggest_project_path(self, file_info: Dict, analysis: Dict) -> Path:
        """Suggest path for project directories"""
        project_name = file_info["path"].name

        if analysis.get("is_git"):
            # Git projects go to /github/{project_name}
            return self.root_path / "github" / project_name
        else:
            # Non-git projects go to /local/code/{project_name}
            return self.root_path / "local" / "code" / project_name

    def _suggest_large_file_path(self, file_info: Dict, analysis: Dict) -> Path:
        """Suggest path for large files"""
        # Organize by file type within large_files
        file_type = analysis.get("file_type", "misc")
        return self.data_path / "large_files" / file_type / file_info["path"].name

    def _suggest_hidden_file_path(self, file_info: Dict) -> Path:
        """Suggest path for hidden files"""
        # Group by type of hidden file
        name = file_info["path"].name.lower()

        if "config" in name or "rc" in name:
            subdir = "configs"
        elif "cache" in name or "tmp" in name:
            subdir = "cache"
        else:
            subdir = "misc"

        return self.data_path / "hidden_files" / subdir / file_info["path"].name

    def _suggest_image_path(self, file_info: Dict, analysis: Dict) -> Path:
        """Suggest path for images with date-based organization"""
        base_path = self.data_path / "media" / "images"

        # Try to get date from EXIF or file stats
        date = analysis.get("date_taken")
        if not date:
            # Fall back to file modification date
            try:
                stat = file_info["path"].stat()
                date = datetime.fromtimestamp(
                    stat.st_birthtime
                    if hasattr(stat, "st_birthtime")
                    else stat.st_mtime
                )
            except:
                date = datetime.now()

        # Create year/month structure
        year_month = f"{date.year}/{date.month:02d}"

        # Further categorize by AI analysis if available
        ai_category = analysis.get("ai_category", "")
        if ai_category in ["screenshot", "meme", "document"]:
            return base_path / ai_category / year_month / file_info["path"].name
        else:
            return base_path / year_month / file_info["path"].name

    def _suggest_document_path(self, file_info: Dict, analysis: Dict) -> Path:
        """Suggest path for documents"""
        base_path = self.data_path / "documents"

        # Use AI category if available
        ai_category = analysis.get("ai_category", "")

        category_map = {
            "report": "reports",
            "article": "articles",
            "manual": "manuals",
            "notes": "notes",
            "email": "emails",
            "config": "configs",
            "data": "data_files",
        }

        subdir = category_map.get(ai_category, "general")

        # Add year subdirectory for better organization
        try:
            stat = file_info["path"].stat()
            date = datetime.fromtimestamp(
                stat.st_birthtime if hasattr(stat, "st_birthtime") else stat.st_mtime
            )
            year = str(date.year)
        except:
            year = str(datetime.now().year)

        return base_path / subdir / year / file_info["path"].name

    def _suggest_media_path(self, file_info: Dict, media_type: str) -> Path:
        """Suggest path for media files (video/audio)"""
        base_path = self.data_path / "media" / media_type

        # Organize by year
        try:
            stat = file_info["path"].stat()
            date = datetime.fromtimestamp(
                stat.st_birthtime if hasattr(stat, "st_birthtime") else stat.st_mtime
            )
            year = str(date.year)
        except:
            year = "unknown"

        return base_path / year / file_info["path"].name

    def _suggest_archive_path(self, file_info: Dict) -> Path:
        """Suggest path for archive files"""
        # Simple organization by year
        try:
            stat = file_info["path"].stat()
            date = datetime.fromtimestamp(
                stat.st_birthtime if hasattr(stat, "st_birthtime") else stat.st_mtime
            )
            year = str(date.year)
        except:
            year = "unknown"

        return self.data_path / "archives" / year / file_info["path"].name

    def _suggest_misc_path(self, file_info: Dict, analysis: Dict) -> Path:
        """Suggest path for miscellaneous files"""
        # Group by file extension
        ext = file_info["path"].suffix.lower()
        if ext:
            subdir = ext[1:]  # Remove the dot
        else:
            subdir = "no_extension"

        return self.data_path / "misc" / subdir / file_info["path"].name

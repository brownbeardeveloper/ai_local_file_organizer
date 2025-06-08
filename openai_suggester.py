"""
AI-Enhanced File Organization System with OpenAI Integration
Simplified approach with category-based batch processing
"""

from pathlib import Path
from typing import List, Dict, Optional
import json
import os
import openai
from dotenv import load_dotenv

load_dotenv()


class OpenAIPathPlanner:
    """Uses OpenAI to suggest file organization paths based on metadata and AI insights"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

        if not self.api_key:
            raise RuntimeError("Missing OpenAI API key")

        self.client = openai.OpenAI(api_key=self.api_key)

        # Directory structure mapping - must match mover.py
        self.sub_dirs_map = {
            "documents": ["pdf", "word", "excel"],
            "finance": ["invoices", "receipts"],
            "work": ["projects", "other"],
            "studies": ["notes", "assignments"],
            "health": ["training", "insurance"],
            "photos": ["camera", "phone", "screenshots"],
            "software": ["installers", "configs"],
            "archives": ["zip", "rar"],
            "hidden": [],
            "large": [],
            "misc": [],
            "dev": ["python", "javascript", "java", "other"],
        }

    def suggest_paths(self, file_analyses: List[Dict]) -> Dict[str, str]:
        """Return a mapping from original file path to suggested new path.

        Raises:
            RuntimeError: if input validation fails or processing fails
            TypeError: if input types are incorrect
        """
        self._validate_input(file_analyses)

        categorized_files = self._group_by_category(file_analyses)
        results = {}

        for category, files in categorized_files.items():
            category_results = self._process_category(category, files)
            results.update(category_results)

        return results

    def _validate_input(self, file_analyses: List[Dict]) -> None:
        """Validate input file analyses.

        Raises:
            RuntimeError: if validation fails
            TypeError: if input types are incorrect
        """
        if not isinstance(file_analyses, list):
            raise TypeError(
                f"file_analyses must be a list, got {type(file_analyses).__name__}"
            )

        required_fields = [
            "path",
            "name",
            "category",
            "size",
            "modified",
            "ai_insights",
        ]

        for i, item in enumerate(file_analyses):
            if not isinstance(item, dict):
                raise TypeError(
                    f"file_analyses[{i}] must be a dict, got {type(item).__name__}"
                )

            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                available_fields = list(item.keys())
                raise RuntimeError(
                    f"file_analyses[{i}] missing required fields: {missing_fields}. "
                    f"Available fields: {available_fields}. "
                    f"Required fields: {required_fields}"
                )

            self._validate_ai_insights(item["ai_insights"], f"file_analyses[{i}]")

    def _validate_ai_insights(self, ai_insights, context: str) -> None:
        """Validate ai_insights field.

        Raises:
            TypeError: if ai_insights is not a dict
            RuntimeError: if AI analysis failed
        """
        if not isinstance(ai_insights, dict):
            raise TypeError(
                f"{context}['ai_insights'] must be a dict, got {type(ai_insights).__name__}"
            )

        if "error" in ai_insights:
            raise RuntimeError(f"AI analysis failed: {ai_insights['error']}")

    def _group_by_category(self, file_analyses: List[Dict]) -> Dict[str, List[Dict]]:
        """Group files by their category.

        Returns:
            Dictionary mapping category names to lists of file analyses
        """
        categorized = {}
        for file_analysis in file_analyses:
            category = file_analysis.get("category", "unknown")
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(file_analysis)
        return categorized

    def _process_category(self, category: str, files: List[Dict]) -> Dict[str, str]:
        """Process all files in a single category with one API call.

        Raises:
            RuntimeError: if OpenAI API call fails
        """
        prompt = self._build_category_prompt(category, files)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_instructions(category)},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=4000,
        )

        return self._parse_response(response.choices[0].message.content)

    def _build_category_prompt(self, category: str, files: List[Dict]) -> str:
        """Build prompt for a specific category of files.

        Raises:
            RuntimeError: if file data processing fails
        """
        file_data = []

        for f in files:
            data = {
                "original_path": f["path"],
                "name": f["name"],
                "category": f["category"],
                "size": f["size"],
                "modified": f["modified"],
                "ai_insights": f["ai_insights"],
            }

            # Add category-specific fields
            if category == "image":
                data["mime_type"] = f.get("mime_type", "")
            elif category == "document":
                data["suffix"] = f.get("suffix", "")

            file_data.append(data)

        return f"""Below is a list of {category} files with AI-generated metadata. 
Your task is to suggest well-structured, logical destination paths.

{self._get_directory_structure_info()}

{self._get_category_rules(category)}

CRITICAL RULES:
- MUST use structure: main_category/sub_category/YYYY/filename.ext
- Valid categories: {", ".join(self.sub_dirs_map.keys())}
- Use year from 'modified' date as subfolder
- Generate new descriptive filenames based on AI insights - NEVER keep original names
- Simple names from primary object: "person.jpg", "building.jpg", "food.jpg"
- For duplicates: person2.jpg, person3.jpg (NO underscores)
- Output valid JSON: {{"original_path": "new_path"}}
- Relative paths only

File list:
{json.dumps(file_data, indent=2)}"""

    def _get_category_rules(self, category: str) -> str:
        """Get category-specific organization rules."""
        category_rules = {
            "image": "photos/[camera|phone|screenshots]/YYYY/ → person.jpg, building.jpg, food.jpg",
            "document": "documents/[pdf|word|excel]/YYYY/ → report.pdf, invoice.pdf, letter.docx",
            "video": "work/projects/YYYY/ OR misc/YYYY/ → presentation.mp4, family.mp4",
            "audio": "work/projects/YYYY/ OR misc/YYYY/ → recording.mp3, music.mp3",
            "archive": "archives/[zip|rar]/YYYY/ → backup.zip, project.rar",
            "code": "dev/[python|javascript|java|other]/YYYY/ → script.py, app.js",
        }
        return category_rules.get(category, "misc/YYYY/ → descriptive_filename.ext")

    def _get_directory_structure_info(self) -> str:
        """Provide directory structure information."""
        lines = ["DIRECTORY STRUCTURE:"]
        for main_cat, sub_cats in self.sub_dirs_map.items():
            if sub_cats:
                lines.append(f"- {main_cat}/ → {', '.join(sub_cats)}")
            else:
                lines.append(f"- {main_cat}/ → direct year folders")
        return "\n".join(lines)

    def _get_system_instructions(self, category: str) -> str:
        """Get system instructions tailored for the category."""
        return f"""Professional file system architect for {category} files.
Create logical, maintainable folder structures using AI insights for intelligent categorization.
Follow directory structure exactly, generate descriptive filenames, ensure scalability."""

    def _parse_response(self, raw: str) -> Dict[str, str]:
        """Parse OpenAI response into path mapping.

        Raises:
            ValueError: if JSON parsing fails
        """
        content = raw.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]

        return json.loads(content)

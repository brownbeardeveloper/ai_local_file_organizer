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
            try:
                category_results = self._process_category(category, files)
                results.update(category_results)
            except Exception as e:
                print(f"ERROR in category '{category}': {e}")
                # Continue with other categories instead of failing completely

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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_instructions(category),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=4000,
            )

            raw_response = response.choices[0].message.content
            parsed_result = self._parse_response(raw_response)
            return parsed_result

        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed for category '{category}': {e}")

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

        return f"""You are sorting {category} files into logical and organized folders based on AI-generated metadata.

        TASK:
        - Suggest precise, logical file paths using the given directory rules.
        - Output must be VALID JSON only, formatted as {{"original_path": "new_path"}}.

        DIRECTORY STRUCTURE RULES:
        {self._get_directory_structure_info()}

        CATEGORY-SPECIFIC RULES:
        {self._get_category_rules(category)}

        CRITICAL REQUIREMENTS:
        1. Folder structure MUST follow: main_category/sub_category/YYYY/filename.ext
        2. Allowed main categories: {", ".join(self.sub_dirs_map.keys())}
        3. The 'YYYY' folder is the YEAR from the file's 'modified' date.
        4. Preserve EXACT original file extension (.jpeg remains .jpeg, .JPG remains .JPG).
        5. Generate NEW descriptive filenames based solely on AI insights (NEVER use original names).
        - Examples: "person.jpg", "building.jpg", "food.jpg".
        6. Similar files share the same base filename (multiple resumes → "resume.pdf").
        7. NEVER add numbers or identifiers; duplicates are handled automatically.
        8. Paths must be RELATIVE, no absolute paths allowed.

        SPECIAL RULES FOR FINANCIAL FILES:
        - 'budget' files → finance/invoices/YYYY/budget.txt
        - 'invoice' files → finance/invoices/YYYY/invoice.pdf
        - 'insurance' files → finance/invoices/YYYY/insurance.pdf
        - All financial documents use 'finance/' instead of 'documents/'.

        FILES TO ORGANIZE:
        {json.dumps(file_data, indent=2)}"""

    def _get_category_rules(self, category: str) -> str:
        """Get category-specific organization rules."""
        category_rules = {
            "image": "photos/[camera|phone|screenshots]/YYYY/ → person.jpg, building.jpg, food.jpg",
            "document": "documents/[pdf|word|excel]/YYYY/ → report.pdf, invoice.pdf, letter.docx\n"
            + "finance/[invoices|receipts]/YYYY/ → budget.txt, expense.pdf, receipt.jpg (for budget/financial content)",
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
        """Provide clear, structured instructions for file categorization."""
        return f"""You are a professional organizer specialized in {category} files.

        TASK:
        - Create a logical and clear folder structure.
        - Use concise, descriptive folder and file names.
        - Sort files neatly based on their content.

        REQUIREMENTS:
        - Keep the structure simple and easy to maintain.
        - Make sure it can easily grow with more files in the future.
        - Clearly separate different file types or topics.

        Follow these instructions exactly."""

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

        try:
            parsed_json = json.loads(content)

            # Handle both array format and object format
            if isinstance(parsed_json, list):
                # Convert array format to dictionary mapping
                result = {}
                for item in parsed_json:
                    if (
                        isinstance(item, dict)
                        and "original_path" in item
                        and "new_path" in item
                    ):
                        result[item["original_path"]] = item["new_path"]
                return result
            elif isinstance(parsed_json, dict):
                # Already in the expected format
                return parsed_json
            else:
                raise ValueError(f"Unexpected JSON format: {type(parsed_json)}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")

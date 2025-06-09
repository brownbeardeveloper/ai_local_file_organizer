"""
Ollama Text Analysis
Handles Ollama-based natural language understanding for text content
"""

from typing import Dict, Any
import ollama
from ai_model import AIModel


class OllamaAnalyzer(AIModel):
    """Handles Ollama-based text analysis.

    Raises:
        RuntimeError: If Ollama does not respond or the daemon is not running.
        ValueError: If the specified model name is not found among available Ollama models.
    """

    def __init__(self, model_name: str = "qwen3:1.7b"):
        """Initialize with default qwen3:1.7b model or specified model."""
        super().__init__(model_name)

    def _load_model(self):
        """Check if the specified Ollama model is available and set it for use."""
        models = ollama.list()

        if not models or "models" not in models:
            raise RuntimeError("No response from Ollama. Is the daemon running?")

        available = {m["model"] for m in models["models"]}

        if self.model_name in available:
            self.model = self.model_name
        else:
            raise ValueError(
                f"Ollama model '{self.model_name}' not found. Available: {sorted(available)}"
            )

    def analyze_text(
        self, text_content: str, analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """Analyze text content using Ollama with improved prompts.

        Raises:
            RuntimeError: If Ollama is unavailable or not running.
        Returns:
            Dict[str, Any]: The analysis result, or an error indicator if analysis fails.
        """
        if not self.is_available():
            raise RuntimeError("Ollama is unavailable or not running.")

        try:
            if analysis_type == "document":
                prompt = f"""You are classifying documents based ONLY on their main content. 

                Document Content:
                {text_content[:800]}

                Classification Instructions:

                Pick exactly ONE category from this list, based on what the document clearly shows or mentions:

                1. BUDGET - mentions personal money, income, expenses, savings, financial plans.
                2. INVOICE - shows billing, payments, transactions, business charges.
                3. MANUAL - gives instructions, how-to guides, tutorials.
                4. REPORT - contains analysis, data findings, business review (NOT personal finance).
                5. RESUME - includes job history, skills, education.
                6. ARTICLE - informative, educational, or blog content.
                7. CERTIFICATE - proves completion or achievement officially.
                8. INSURANCE - discusses policies, coverage, or insurance terms.
                9. EMAIL - written messages or correspondence.
                10. NOTES - informal, personal reminders or thoughts.
                11. OTHER - does NOT clearly match any category above.

                Answer ONLY with the exact category name:"""

            elif analysis_type == "csv":
                prompt = f"""You are classifying CSV data files based ONLY on the type of data shown.

                CSV Data:
                {text_content[:400]}

                Classification Instructions:

                Pick exactly ONE category that clearly matches the data:

                1. financial-transactions - records money, payments, bank transactions.
                2. customer-contacts - includes names, emails, phone numbers, addresses.
                3. inventory-catalog - lists products, items, stock, or SKUs.
                4. employee-data - contains staff info, payroll, HR records.
                5. website-analytics - tracks page views, clicks, user actions.
                6. sales-data - sales, deals, customer purchases, revenues.
                7. sensor-data - IoT measurements, sensor readings.
                8. survey-responses - questionnaire results, feedback.
                9. user-activity - logins, application usage, activity records.

                Answer ONLY with the exact data type:"""

            elif analysis_type == "script":
                prompt = f"""You are classifying script files based ONLY on their main commands and purpose.

                Script Commands and Content:
                {text_content[:400]}

                Classification Instructions:

                Pick exactly ONE category based on the main commands and actions:

                1. NETWORK-MONITORING - ping, curl, wget, netstat, nmap, ssh, connectivity checks.
                2. BACKUP-AUTOMATION - tar, zip, rsync, copying or archiving files.
                3. LOG-ANALYSIS - grep, awk, sed, tail, head, parsing logs.
                4. WEB-SCRAPER - curl, wget, requests, downloading data from websites.
                5. DATA-PROCESSING - sort, uniq, cut, data transformations or calculations.
                6. SYSTEM-ADMIN - useradd, chmod, systemctl, managing system services.
                7. DEPLOYMENT-SCRIPT - docker, kubectl, npm install, deploying apps.
                8. FILE-MANAGEMENT - find, rm, mkdir, organizing files or directories.

                Answer ONLY with the exact purpose:"""

            else:
                prompt = f"Analyze this content: {text_content[:500]}..."

            response = ollama.chat(
                model=self.model, messages=[{"role": "user", "content": prompt}]
            )

            content_type = self._extract_answer(response["message"]["content"])
            return {"content": content_type}

        except Exception:
            return {"content": "ai_analysis_failed"}

    def _extract_answer(self, response_text: str) -> str:
        """Extract the actual answer from potentially verbose response"""

        # Remove thinking tags if present
        if "<think>" in response_text and "</think>" in response_text:
            # Extract content after </think>
            parts = response_text.split("</think>")
            if len(parts) > 1:
                response_text = parts[-1]

        response = response_text.strip().lower()

        # Look for known answer patterns
        valid_answers = {
            # Document types
            "budget",
            "resume",
            "report",
            "invoice",
            "manual",
            "article",
            "email",
            "notes",
            "insurance",
            "certificate",
            "other",
            # CSV types
            "financial-transactions",
            "customer-contacts",
            "website-analytics",
            "inventory-catalog",
            "employee-data",
            "sensor-data",
            "sales-data",
            "user-activity",
            "survey-responses",
            # Script types
            "network-monitoring",
            "backup-automation",
            "log-analysis",
            "web-scraper",
            "data-processing",
            "system-admin",
            "deployment-script",
            "file-management",
        }

        # If response is already a valid answer, return it
        if response in valid_answers:
            return response

        # Try to find a valid answer in the response text
        for answer in valid_answers:
            if answer in response:
                return answer

        # If no valid answer found, return cleaned first few words
        words = response.replace(" ", "-").split("-")[:3]
        return "-".join(words) if words else "unknown"

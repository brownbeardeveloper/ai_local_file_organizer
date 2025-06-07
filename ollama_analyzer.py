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

    def __init__(self, model_name: str = "qwen3:4b"):
        """Initialize with default qwen3:4b model or specified model."""
        super().__init__(model_name)

    def _load_model(self):
        """Check if the specified Ollama model is available and set it for use."""
        models = ollama.list()

        if not models or "models" not in models:
            raise RuntimeError("No response from Ollama. Is the daemon running?")

        available = {m["model"] for m in models["models"]}

        if self.model_name in available:
            self.model = self.model_name
            print(f"Using Ollama model: {self.model}")
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
                prompt = f"""You are an expert document classifier. Read the content and understand what type of document this is:

            {text_content[:800]}

            CLASSIFICATION LOGIC:
            1. MANUAL - If it explains how to do something, contains instructions, tutorials, or guides
            2. REPORT - If it analyzes data, presents findings, or business analysis
            3. RESUME - If it lists someone's work experience, education, and skills for job applications
            4. ARTICLE - If it's informational content, blog posts, or educational material
            5. CERTIFICATE - If it's an official document proving completion or achievement  
            6. INSURANCE - If it contains policy terms, coverage details, or insurance conditions
            7. INVOICE - If it contains billing information, payment details, or financial transactions
            8. EMAIL - If it's correspondence or communication
            9. NOTES - If it's personal thoughts, reminders, or informal documentation
            10. OTHER - If it doesn't fit the above categories

            FOCUS ON THE MAIN PURPOSE AND CONTENT:
            - What is this document trying to accomplish?
            - Is it teaching, proving, billing, communicating, or documenting?
            - Look at the structure and language used

            Categories: manual, report, resume, article, certificate, insurance, invoice, email, notes, other

            Answer with ONLY the category:"""

            elif analysis_type == "csv":
                prompt = f"""You are a librarian organizing data files to help people find them easily on their computer.

            Look at this CSV data:
            {text_content[:400]}

            What kind of data is this? Think like a librarian - what label would help someone find this file when they need it?

            Common data types:
            - financial-transactions (money, payments, purchases, deposits, bank records)
            - customer-contacts (names, emails, phone numbers, addresses)
            - inventory-catalog (products, items, stock, SKU numbers)
            - employee-data (staff information, HR records, payroll)
            - website-analytics (page views, clicks, user behavior)
            - sales-data (deals, revenue, customer purchases)
            - sensor-data (measurements, readings, IoT data)
            - survey-responses (questionnaire answers, feedback)
            - user-activity (login logs, app usage, activity records)

            Answer with the data type:"""

            elif analysis_type == "script":
                prompt = f"""You are a librarian organizing script files to help people find them easily on their computer.

            Look at this script and focus on the KEY COMMANDS:
            {text_content[:400]}

            What is the MAIN PURPOSE? Look for these specific indicators:

            NETWORK-MONITORING if you see: ping, curl, wget, netstat, nmap, ssh, nc (netcat), telnet - testing connectivity or checking if servers/websites are up/down
            BACKUP-AUTOMATION if you see: tar, zip, rsync, cp, mv for saving/archiving files  
            LOG-ANALYSIS if you see: grep, awk, sed, tail, head for reading/parsing logs
            WEB-SCRAPER if you see: curl, wget, requests downloading from URLs/websites
            DATA-PROCESSING if you see: sort, uniq, cut, calculations, file transformations
            SYSTEM-ADMIN if you see: useradd, chmod, systemctl, service management
            DEPLOYMENT-SCRIPT if you see: docker, kubectl, npm install, app deployment
            FILE-MANAGEMENT if you see: find, rm, mkdir, organizing directories

            Look at the COMMANDS and COMMENTS - what is this script actually doing?

            Answer with just the purpose:"""

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

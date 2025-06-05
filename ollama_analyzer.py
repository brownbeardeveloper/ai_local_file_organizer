"""
Ollama Text Analysis
Handles Ollama-based natural language understanding for text content
"""

from typing import Dict, Any
import ollama
from ai_model import AIModel


class OllamaAnalyzer(AIModel):
    """Handles Ollama-based text analysis"""

    def _load_model(self):
        """Select and configure Ollama model"""
        try:
            models_list = ollama.list()
            available_models = [m["model"] for m in models_list.get("models", [])]

            if self.model_name in available_models:
                print(f"Using Ollama model: {self.model_name}")
                self.model = self.model_name
            elif available_models:
                print(f"Using fallback Ollama model: {available_models[0]}")
                self.model = available_models[0]
            else:
                print("No Ollama models found. Install with: ollama pull mistral")
                self.model = None

        except Exception as e:
            print(f"Ollama setup error: {e}")
            self.model = None

    def analyze_text(
        self, text_content: str, analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """Use Ollama to analyze text content with improved prompts"""
        if not self.is_available():
            return {"content": "ollama_unavailable"}

        try:
            if analysis_type == "document":
                prompt = f"""You are an expert document classifier. Analyze this document content:

{text_content[:800]}

SWEDISH/ENGLISH KEYWORDS TO RECOGNIZE:
- CV/Resume: "Curriculum Vitae", "CV", "Arbetslivserfarenhet", "Utbildning", "work experience", "education", "skills", "Färdigheter"
- Insurance: "försäkring", "insurance", "terms", "villkor", "Tryg", "policy"
- Certificate: "betyg", "tjänstgöringsbetyg", "certificate", "diploma", "certifiering"

CLASSIFICATION RULES:
1. If document contains work history/experience + education + skills → "resume"
2. If document contains insurance terms/conditions → "insurance" 
3. If document contains certificates/diplomas → "certificate"
4. If document contains business analysis → "report"
5. If document contains instructions → "manual"
6. If document contains personal thoughts → "notes"

Look for these exact patterns:
- "Curriculum Vitae" or "CV" + "Arbetslivserfarenhet" = resume
- "Utbildning" + "Färdigheter" + work history = resume
- "insurance" or "försäkring" + terms = insurance
- "betyg" or "certificate" = certificate

Categories: resume, insurance, certificate, report, invoice, manual, notes, email, other

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
            "config",
            "script",
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

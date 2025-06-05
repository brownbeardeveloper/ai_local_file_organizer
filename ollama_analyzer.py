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
        """Use Ollama to analyze text content"""
        if not self.is_available():
            return {"content": "ollama_unavailable"}

        try:
            if analysis_type == "document":
                prompt = f"""Analyze this text and categorize what type of content it is. Reply with ONE word from:
                
                [notes, code, email, article, resume, invoice, manual, recipe, list, diary, report, config, other]
                
                Text preview: {text_content[:500]}..."""
            else:
                prompt = f"Analyze this text content: {text_content[:500]}..."

            response = ollama.chat(
                model=self.model, messages=[{"role": "user", "content": prompt}]
            )

            content_type = response["message"]["content"].strip().lower()
            return {"content": content_type}

        except Exception:
            return {"content": "ai_analysis_failed"}

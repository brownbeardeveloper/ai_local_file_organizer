"""
File Analyzer Module
Analyzes file content using Ollama LLM and ResNet for images
"""

import warnings
import mimetypes
import magic
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import exifread
from PIL import Image
import torch
import torchvision.models as models
import torchvision.transforms as transforms
import ollama

class FileAnalyzer:
    def __init__(self):
        self.setup_models()

        # File size threshold (100MB)
        self.large_file_threshold = 100 * 1024 * 1024

        # Initialize mimetypes
        mimetypes.init()

    def setup_models(self):
        """Setup AI models for analysis"""
        # Setup ResNet152 for image analysis (better than ResNet50 for M1)
        try:
            self.device = torch.device(
                "mps" if torch.backends.mps.is_available() else "cpu"
            )
            # Use the new weights parameter instead of deprecated pretrained

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.resnet = models.resnet152(
                    weights=models.ResNet152_Weights.IMAGENET1K_V1
                )
            self.resnet.to(self.device)
            self.resnet.eval()

            # Image preprocessing
            self.preprocess = transforms.Compose(
                [
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                    ),
                ]
            )

            # Load ImageNet class labels
            self.load_imagenet_classes()
            print("ResNet152 loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load ResNet152: {e}")
            self.resnet = None

        # Check Ollama models
        try:
            models_list = ollama.list()
            if not models_list or "models" not in models_list:
                raise Exception("Ollama service not running or no models available")

            available_models = [m["name"] for m in models_list["models"]]

            # Recommended models for M1 Mac
            recommended = ["mistral:latest", "llama2:latest", "phi:latest"]
            self.ollama_model = None

            for model in recommended:
                if model in available_models:
                    self.ollama_model = model
                    print(f"Using Ollama model: {model}")
                    break

            if not self.ollama_model and available_models:
                self.ollama_model = available_models[0]
                print(
                    f"Using available Ollama model: {self.ollama_model}"
                )

            if not self.ollama_model:
                print(
                    "No Ollama models found. Install with: ollama pull mistral"
                )
        except Exception as e:
            # More graceful Ollama handling - don't show the raw error
            if "Ollama service not running" in str(e) or "Connection" in str(e):
                print(
                    "Ollama not running. AI text analysis disabled."
                )
            else:
                print(
                    "Ollama not available. AI text analysis disabled."
                )
            self.ollama_model = None

    def load_imagenet_classes(self):
        """Load ImageNet class labels"""
        try:
            # Basic categories for common objects
            self.imagenet_categories = {
                "person": ["person", "face", "people"],
                "animal": ["dog", "cat", "bird", "fish", "animal"],
                "food": ["food", "meal", "dish", "fruit", "vegetable"],
                "nature": ["mountain", "beach", "forest", "tree", "landscape"],
                "vehicle": ["car", "bicycle", "motorcycle", "bus", "train"],
                "electronics": ["computer", "phone", "screen", "keyboard"],
                "document": ["document", "paper", "text", "book"],
            }
        except:
            self.imagenet_categories = {}

    def analyze(self, file_info: Dict) -> Dict[str, Any]:
        """Analyze a file and return insights"""
        analysis = {
            "file_type": self._get_file_type(file_info["path"]),
            "mime_type": self._get_mime_type(file_info["path"]),
            "is_large": file_info["size"] > self.large_file_threshold,
            "size": file_info["size"],
        }

        # Special handling for projects
        if file_info.get("is_project"):
            analysis["category"] = "project"
            analysis["is_git"] = file_info.get("is_git", False)
            return analysis

        # Analyze based on file type
        if analysis["mime_type"]:
            if analysis["mime_type"].startswith("image/"):
                analysis.update(self._analyze_image(file_info["path"]))
            elif analysis["mime_type"].startswith("text/") or analysis["mime_type"] in [
                "application/pdf",
                "application/json",
            ]:
                analysis.update(self._analyze_text(file_info["path"]))
            elif analysis["mime_type"].startswith("video/"):
                analysis["category"] = "video"
            elif analysis["mime_type"].startswith("audio/"):
                analysis["category"] = "audio"
            elif analysis["mime_type"] in [
                "application/zip",
                "application/x-tar",
                "application/x-rar",
            ]:
                analysis["category"] = "archive"

        # Handle empty files or files without proper mime detection by file extension
        if "category" not in analysis or analysis["mime_type"] == "inode/x-empty":
            # Fall back to file extension for categorization
            file_type = analysis["file_type"]
            if file_type in ["image"]:
                analysis["category"] = "image"
            elif file_type in ["document"]:
                analysis["category"] = "document"
            elif file_type in ["video"]:
                analysis["category"] = "video"
            elif file_type in ["audio"]:
                analysis["category"] = "audio"
            elif file_type in ["archive"]:
                analysis["category"] = "archive"
            else:
                analysis["category"] = "misc"

        # Handle hidden files
        if file_info.get("type") == "hidden_file":
            analysis["category"] = "hidden"

        return analysis

    def _get_file_type(self, path: Path) -> str:
        """Get file type based on extension"""
        ext = path.suffix.lower()

        # Common file type mappings
        type_map = {
            ".pdf": "document",
            ".doc": "document",
            ".docx": "document",
            ".txt": "document",
            ".md": "document",
            ".jpg": "image",
            ".jpeg": "image",
            ".png": "image",
            ".gif": "image",
            ".mp4": "video",
            ".avi": "video",
            ".mov": "video",
            ".mp3": "audio",
            ".wav": "audio",
            ".flac": "audio",
            ".zip": "archive",
            ".tar": "archive",
            ".gz": "archive",
            ".rar": "archive",
            ".py": "code",
            ".js": "code",
            ".ts": "code",
            ".jsx": "code",
            ".tsx": "code",
        }

        return type_map.get(ext, "misc")

    def _get_mime_type(self, path: Path) -> Optional[str]:
        """Get MIME type of file"""
        try:
            # Try python-magic first
            mime = magic.from_file(str(path), mime=True)
            return mime
        except:
            # Fallback to mimetypes
            mime_type, _ = mimetypes.guess_type(str(path))
            return mime_type

    def _analyze_image(self, path: Path) -> Dict[str, Any]:
        """Analyze image content and metadata"""
        result = {"category": "image"}

        try:
            # Extract EXIF data for date
            with open(path, "rb") as f:
                tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
                if "EXIF DateTimeOriginal" in tags:
                    date_str = str(tags["EXIF DateTimeOriginal"])
                    try:
                        result["date_taken"] = datetime.strptime(
                            date_str, "%Y:%m:%d %H:%M:%S"
                        )
                    except:
                        pass

            # Use ResNet for content classification
            if self.resnet:
                image = Image.open(path).convert("RGB")
                input_tensor = self.preprocess(image)
                input_batch = input_tensor.unsqueeze(0).to(self.device)

                with torch.no_grad():
                    output = self.resnet(input_batch)
                    _, predicted = torch.max(output, 1)

                    # Get top predictions
                    probabilities = torch.nn.functional.softmax(output[0], dim=0)
                    top5_prob, top5_class = torch.topk(probabilities, 5)

                    # Simple categorization based on predictions
                    result["ai_category"] = self._categorize_image_prediction(
                        top5_class
                    )
                    result["confidence"] = float(top5_prob[0])

            # Use Ollama for more detailed analysis if available
            if self.ollama_model and result.get("ai_category") == "misc":
                # Only for ambiguous images
                result.update(self._analyze_with_ollama(path, "image"))

        except Exception as e:
            print(f"[dim]Could not analyze image {path.name}: {e}[/dim]")

        return result

    def _categorize_image_prediction(self, predictions) -> str:
        """Categorize image based on ResNet predictions"""
        # This is simplified - in real implementation you'd map ImageNet classes
        # For now, return generic categories
        return "image"  # Would be more specific with proper ImageNet mapping

    def _analyze_text(self, path: Path) -> Dict[str, Any]:
        """Analyze text content"""
        result = {"category": "document"}

        if (
            not self.ollama_model or path.stat().st_size > 1024 * 1024
        ):  # Skip large files
            return result

        try:
            result.update(self._analyze_with_ollama(path, "text"))
        except Exception as e:
            print(f"[dim]Could not analyze text {path.name}: {e}[/dim]")

        return result

    def _analyze_with_ollama(self, path: Path, file_type: str) -> Dict[str, Any]:
        """Use Ollama to analyze file content"""
        try:
            if file_type == "text":
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(5000)  # Read first 5000 chars

                prompt = f"""Analyze this text content and categorize it. Reply with ONLY one word from: 
                [document, code, config, data, notes, report, email, article, manual, other]
                
                Content: {content[:1000]}..."""

            else:  # image
                prompt = """Based on an image analysis, suggest if this image belongs to:
                [personal, work, screenshot, meme, document, nature, product, other]
                Reply with ONLY one word."""

            response = ollama.chat(
                model=self.ollama_model, messages=[{"role": "user", "content": prompt}]
            )

            category = response["message"]["content"].strip().lower()
            return {"ai_category": category}

        except Exception as e:
            return {}

    def _get_file_date(self, path: Path) -> Optional[datetime]:
        """Get file creation or modification date"""
        try:
            stat = path.stat()
            # Use creation time on macOS
            return datetime.fromtimestamp(
                stat.st_birthtime if hasattr(stat, "st_birthtime") else stat.st_mtime
            )
        except:
            return None

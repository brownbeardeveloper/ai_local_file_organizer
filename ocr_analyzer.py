"""
OCR Text Extraction Analyzer
Handles multi-language text extraction from images and scanned documents
"""

from typing import Dict, Any
from pathlib import Path
from ai_model import AIModel
from paddleocr import PaddleOCR


class OCRAnalyzer(AIModel):
    """Handles OCR-based text extraction from images and scanned documents"""

    def __init__(
        self,
        languages: list = None,
    ):
        """
        Initialize OCR analyzer - Always uses PaddleOCR optimized for Swedish

        Args:
            languages: List of language codes (default: ['sv', 'en'] - Swedish prioritized)
        """
        self.languages = languages or ["sv", "en"]  # Swedish first, then English

        # Always use PaddleOCR
        self.primary_engine = "paddleocr"
        super().__init__(self.primary_engine)

    def _load_model(self):
        """Initialize PaddleOCR engine"""
        try:
            self.paddle_reader = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                use_gpu=False,
                show_log=False,
            )
            print("PaddleOCR loaded")
            self.model = "paddleocr_ready"

        except Exception as e:
            print(f"PaddleOCR initialization error: {e}")
            raise RuntimeError(f"Failed to initialize PaddleOCR: {e}")

    def extract_text_from_image(self, image_path: Path) -> Dict[str, Any]:
        """Extract text from image file using PaddleOCR"""
        if not self.is_available():
            return {"text": "", "confidence": 0, "engine": "none"}

        try:
            return self._extract_with_paddleocr(image_path)

        except Exception as e:
            print(f"PaddleOCR extraction failed: {e}")
            return {"text": "", "confidence": 0, "engine": "failed"}

    def extract_text_from_pdf(
        self, pdf_path: Path, max_pages: int = 3
    ) -> Dict[str, Any]:
        """Extract text from scanned PDF using OCR"""
        if not self.is_available():
            return {"text": "", "confidence": 0, "engine": "none"}

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            text_results = []
            confidences = []

            # Process first few pages only to save resources
            pages_to_process = min(max_pages, len(doc))

            for page_num in range(pages_to_process):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")

                # Extract text from page image using PaddleOCR
                page_result = self._extract_from_image_data_paddle(img_data)

                text_results.append(page_result["text"])
                confidences.append(page_result["confidence"])

            doc.close()

            combined_text = " ".join(text_results)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "text": combined_text,
                "confidence": avg_confidence,
                "engine": self.primary_engine,
                "pages_processed": pages_to_process,
            }

        except Exception as e:
            print(f"PDF OCR extraction failed: {e}")
            return {"text": "", "confidence": 0, "engine": "failed"}

    def _extract_with_paddleocr(self, image_path: Path) -> Dict[str, Any]:
        """Extract text using PaddleOCR"""
        results = self.paddle_reader.ocr(str(image_path), cls=True)

        # PaddleOCR returns nested list: [[[bbox], (text, confidence)], ...]
        text_parts = []
        confidences = []

        if results and results[0]:
            for line in results[0]:
                if line and len(line) >= 2:
                    text, confidence = line[1]
                    if confidence > 0.5:  # Filter low-confidence results
                        text_parts.append(text)
                        confidences.append(confidence)

        combined_text = " ".join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            "text": combined_text,
            "confidence": avg_confidence,
            "engine": "paddleocr",
            "language_detected": "auto",
        }

    def _extract_from_image_data_paddle(self, image_data: bytes) -> Dict[str, Any]:
        """Extract text from image data using PaddleOCR"""
        import numpy as np
        from PIL import Image
        import io

        # Convert bytes to PIL Image then to numpy array
        image = Image.open(io.BytesIO(image_data))
        img_array = np.array(image)

        results = self.paddle_reader.ocr(img_array, cls=True)

        text_parts = []
        confidences = []

        if results and results[0]:
            for line in results[0]:
                if line and len(line) >= 2:
                    text, confidence = line[1]
                    if confidence > 0.5:
                        text_parts.append(text)
                        confidences.append(confidence)

        combined_text = " ".join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            "text": combined_text,
            "confidence": avg_confidence,
            "engine": "paddleocr",
        }

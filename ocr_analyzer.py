"""
OCR Text Extraction Analyzer
Handles multi-language text extraction from images and scanned documents
Optimized for memory-constrained environments
"""

import io
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
from ai_model import AIModel
from paddleocr import PaddleOCR


class OCRAnalyzer(AIModel):
    """
    High-performance OCR analyzer with memory optimization

    Features:
    - Memory-efficient processing for resource-constrained systems
    - Configurable confidence thresholds and batch processing
    - Multi-language support with Swedish prioritization
    - Fail-fast error handling for production reliability
    """

    def __init__(
        self,
        language: str = "en",
        confidence_threshold: float = 0.6,
        max_pages_per_pdf: int = 2,
    ):
        """
        Initialize OCR analyzer with memory optimization

        Args:
            language: Language code for text recognition (default: "en")
            confidence_threshold: Minimum confidence for text extraction (0.0-1.0)
            max_pages_per_pdf: Max PDF pages to process for memory efficiency
        """
        self.language = language
        self.confidence_threshold = confidence_threshold
        self.max_pages_per_pdf = max_pages_per_pdf

        super().__init__("paddleocr")

    def _load_model(self):
        """Initialize PaddleOCR with GPU acceleration"""
        self.model = PaddleOCR(
            use_angle_cls=True,
            lang=self.language,
            use_gpu=True,
            show_log=False,
            enable_mkldnn=False,  # CPU optimization
            use_tensorrt=True,  # GPU optimization
        )

    def extract_text_from_image(self, image_path: Path) -> Dict[str, Any]:
        """Extract text from image file using OCR"""
        results = self.model.ocr(str(image_path), cls=True)
        return self._process_ocr_results(results, "image")

    def extract_text_from_pdf(
        self, pdf_path: Path, max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract text from PDF using OCR

        Args:
            pdf_path: Path to PDF file
            max_pages: Override default page limit if needed
        """
        doc = fitz.open(pdf_path)
        text_results = []
        confidences = []

        total_pages = len(doc)
        pages_to_process = min(self.max_pages_per_pdf, total_pages)

        for page_num in range(pages_to_process):
            page = doc.load_page(page_num)
            matrix = fitz.Matrix(1.5, 1.5)
            pix = page.get_pixmap(matrix=matrix)
            img_data = pix.tobytes("png")
            pix = None

            page_result = self._extract_from_image_data(img_data)
            text_results.append(page_result["text"])
            confidences.append(page_result["confidence"])
            img_data = None

        doc.close()

        combined_text = " ".join(filter(None, text_results))
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "text": combined_text,
            "confidence": round(avg_confidence, 3),
            "engine": "paddleocr",
            "pages_processed": pages_to_process,
            "total_pages": total_pages,
        }

    def _extract_from_image_data(self, image_data: bytes) -> Dict[str, Any]:
        """Extract text from image data bytes"""
        image = Image.open(io.BytesIO(image_data))
        img_array = np.array(image, dtype=np.uint8)
        image.close()

        results = self.model.ocr(img_array, cls=True)
        return self._process_ocr_results(results, "pdf_page")

    def _process_ocr_results(self, results: Any, source_type: str) -> Dict[str, Any]:
        """
        Process OCR results with confidence filtering

        Args:
            results: Raw OCR results from PaddleOCR
            source_type: Source type ("image" or "pdf_page")
        """
        text_parts = []
        confidences = []

        if results and results[0]:
            for line in results[0]:
                if line and len(line) >= 2:
                    text, confidence = line[1]

                    if confidence >= self.confidence_threshold:
                        text_parts.append(text.strip())
                        confidences.append(confidence)

        combined_text = " ".join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "text": combined_text,
            "confidence": round(avg_confidence, 3),
            "engine": "paddleocr",
            "source_type": source_type,
            "extracted_lines": len(text_parts),
        }

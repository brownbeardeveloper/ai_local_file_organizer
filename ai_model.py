"""
Abstract base class for AI models
"""

from abc import ABC, abstractmethod


class AIModel(ABC):
    """Abstract base class for all AI models"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self._load_model()

    @abstractmethod
    def _load_model(self):
        """Load the specific AI model"""
        pass

    def is_available(self) -> bool:
        """Check if the model is loaded and available"""
        return self.model is not None

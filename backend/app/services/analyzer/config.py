from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class AnalyzerConfig:
    """Конфигурация для анализатора отзывов"""
    model_path: Optional[str] = None
    max_len: int = 192
    confidence_threshold: float = 0.75
    max_workers: int = 4
    cache_size: int = 1000
    max_text_length: int = 10000
    min_aspect_length: int = 2
    similarity_threshold: float = 0.8
    
    def __post_init__(self):
        if self.model_path is None:
            self.model_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'saved_model'
            ) 
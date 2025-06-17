from .review_analyzer import ReviewAnalyzer
from .config import AnalyzerConfig
from typing import Optional

_review_analyzer: Optional[ReviewAnalyzer] = None

def get_review_analyzer() -> ReviewAnalyzer:
    global _review_analyzer
    if _review_analyzer is None:
        _review_analyzer = ReviewAnalyzer()
    return _review_analyzer

class LazyAnalyzer:
    def __getattr__(self, name):
        analyzer = get_review_analyzer()
        return getattr(analyzer, name)

review_analyzer = LazyAnalyzer()

__all__ = ["ReviewAnalyzer", "AnalyzerConfig", "review_analyzer", "get_review_analyzer"] 
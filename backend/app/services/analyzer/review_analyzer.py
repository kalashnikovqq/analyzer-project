import logging
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from .config import AnalyzerConfig
from .model_loader import ModelLoader
from .text_preprocessor import TextPreprocessor
from .aspect_extractor import AspectExtractor
from .aspect_classifier import AspectClassifier
from .aspect_categorizer import AspectCategorizer
from .aspect_merger import AspectMerger
from .cache import AspectCache

logger = logging.getLogger('review_analyzer')

class ReviewAnalyzer:    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.75):
        self.config = AnalyzerConfig(
            model_path=model_path,
            confidence_threshold=confidence_threshold
        )
        
        self.preprocessor = TextPreprocessor()
        self.model_loader = ModelLoader(self.config)
        self.extractor = AspectExtractor(self.model_loader, self.preprocessor, self.config)
        self.classifier = AspectClassifier(self.preprocessor)
        self.categorizer = AspectCategorizer(self.preprocessor)
        self.merger = AspectMerger(self.preprocessor, self.config)
        self.cache = AspectCache(self.config.cache_size)
    
    def analyze_review(self, review_text: str) -> Dict[str, Any]:
        if not review_text or not isinstance(review_text, str) or len(review_text.strip()) < 5:
            return {
                "sentiment": "neutral",
                "positive_aspects": [],
                "negative_aspects": [],
                "clean_text": ""
            }
        
        clean_text = self.preprocessor.preprocess_review(review_text)
        if not clean_text:
            return {
                "sentiment": "neutral",
                "positive_aspects": [],
                "negative_aspects": [],
                "clean_text": ""
            }
        
        try:
            positive_aspects, negative_aspects = self._get_aspects_with_cache(clean_text)
            sentiment = self._determine_sentiment(positive_aspects, negative_aspects)
            
            return {
                "sentiment": sentiment,
                "positive_aspects": positive_aspects,
                "negative_aspects": negative_aspects,
                "clean_text": clean_text
            }
        
        except Exception as e:
            logger.error(f"Ошибка при анализе отзыва: {e}")
            return {
                "sentiment": "neutral",
                "positive_aspects": [],
                "negative_aspects": [],
                "clean_text": clean_text
            }
    
    def analyze_topics(self, texts: List[str]) -> Dict[str, Any]:
        if not texts:
            return {"topic_summary": {}, "detailed_aspects": []}
        
        def process_text(text_content):
            return self.analyze_review(text_content)
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            analyzed_results = list(executor.map(process_text, texts))
        
        return self._build_topic_summary(analyzed_results)
    
    def analyze_sentiment(self, texts: List[str]) -> Dict[str, Any]:
        results = self.analyze_topics(texts)
        
        pos_aspects = []
        neg_aspects = []
        
        for detail in results.get("detailed_aspects", []):
            pos_aspects.extend(detail.get("positive_aspects", []))
            neg_aspects.extend(detail.get("negative_aspects", []))
        
        pos_counter = Counter(pos_aspects)
        neg_counter = Counter(neg_aspects)
        
        pos_aspects_counted = self.merger.merge_similar_aspects(list(pos_counter.items()))
        neg_aspects_counted = self.merger.merge_similar_aspects(list(neg_counter.items()))
        
        corrected_pros, corrected_cons = self.classifier.correct_aspects(
            pos_aspects_counted, neg_aspects_counted
        )
        
        return {
            "positive_aspects": corrected_pros,
            "negative_aspects": corrected_cons,
            "categorized_positive": self.categorizer.categorize_aspects(corrected_pros),
            "categorized_negative": self.categorizer.categorize_aspects(corrected_cons)
        }
    
    def analyze_sentiment_single(self, text: str) -> Dict[str, Any]:
        result = self.analyze_review(text)
        
        pos_counter = Counter(result["positive_aspects"])
        neg_counter = Counter(result["negative_aspects"])
        
        pos_aspects_counted = list(pos_counter.items())
        neg_aspects_counted = list(neg_counter.items())
        
        corrected_pros, corrected_cons = self.classifier.correct_aspects(
            pos_aspects_counted, neg_aspects_counted
        )
        
        return {
            "sentiment": result["sentiment"],
            "positive_aspects": corrected_pros,
            "negative_aspects": corrected_cons,
            "categorized_positive": self.categorizer.categorize_aspects(corrected_pros),
            "categorized_negative": self.categorizer.categorize_aspects(corrected_cons)
        }
    
    def get_summary_statistics(self, analyzed_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not analyzed_reviews:
            return self._empty_statistics()
        
        sentiments = [review.get("sentiment", "neutral") for review in analyzed_reviews]
        sentiment_counts = Counter(sentiments)
        
        total_reviews = len(analyzed_reviews)
        
        all_positive_aspects = []
        all_negative_aspects = []
        
        for review in analyzed_reviews:
            all_positive_aspects.extend(review.get("positive_aspects", []))
            all_negative_aspects.extend(review.get("negative_aspects", []))
        
        pos_counter = Counter(all_positive_aspects)
        neg_counter = Counter(all_negative_aspects)
        
        top_positive = pos_counter.most_common(10)
        top_negative = neg_counter.most_common(10)
        
        merged_positive = self.merger.merge_similar_aspects(list(pos_counter.items()))[:10]
        merged_negative = self.merger.merge_similar_aspects(list(neg_counter.items()))[:10]
        
        return {
            "total_reviews": total_reviews,
            "sentiment_distribution": dict(sentiment_counts),
            "sentiment_percentages": {
                sentiment: (count / total_reviews) * 100 
                for sentiment, count in sentiment_counts.items()
            },
            "top_positive_aspects": top_positive,
            "top_negative_aspects": top_negative,
            "merged_positive_aspects": merged_positive,
            "merged_negative_aspects": merged_negative,
            "categorized_positive": self.categorizer.categorize_aspects(merged_positive),
            "categorized_negative": self.categorizer.categorize_aspects(merged_negative)
        }
    
    def merge_similar_aspects(self, aspects: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        return self.merger.merge_similar_aspects(aspects)
    
    def categorize_aspects(self, aspects: List[Tuple[str, int]]) -> Dict[str, List[Tuple[str, int]]]:
        return self.categorizer.categorize_aspects(aspects)
    
    def classify_and_correct_aspects(self, pros: List[Tuple[str, int]], cons: List[Tuple[str, int]]) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
        return self.classifier.correct_aspects(pros, cons)
    
    @staticmethod
    def preprocess_review(review: str) -> str:
        preprocessor = TextPreprocessor()
        return preprocessor.preprocess_review(review)
    
    @staticmethod
    def lemmatize_text(text: str) -> str:
        preprocessor = TextPreprocessor()
        return preprocessor.lemmatize_text(text)
    
    def _get_aspects_with_cache(self, text: str) -> tuple:
        cached_result = self.cache.get(text)
        if cached_result is not None:
            return cached_result
        
        result = self.extractor.extract_aspects(text)
        self.cache.set(text, result)
        return result
    
    def _determine_sentiment(self, positive_aspects: List[str], negative_aspects: List[str]) -> str:
        pos_count = len(positive_aspects)
        neg_count = len(negative_aspects)
        
        if pos_count > neg_count and pos_count > 0:
            return "positive"
        elif neg_count > pos_count and neg_count > 0:
            return "negative"
        elif pos_count == 0 and neg_count == 0:
            return "neutral"
        else:
            return "mixed"
    
    def _build_topic_summary(self, analyzed_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_positive = []
        all_negative = []
        
        for result in analyzed_results:
            all_positive.extend(result.get("positive_aspects", []))
            all_negative.extend(result.get("negative_aspects", []))
        
        pos_counter = Counter(all_positive)
        neg_counter = Counter(all_negative)
        
        final_topic_summary = {
            "positive_aspects": dict(pos_counter.most_common(20)),
            "negative_aspects": dict(neg_counter.most_common(20)),
            "total_positive_mentions": sum(pos_counter.values()),
            "total_negative_mentions": sum(neg_counter.values())
        }
        
        return {
            "topic_summary": final_topic_summary,
            "detailed_aspects": analyzed_results
        }
    
    def _empty_statistics(self) -> Dict[str, Any]:
        return {
            "total_reviews": 0,
            "sentiment_distribution": {},
            "sentiment_percentages": {},
            "top_positive_aspects": [],
            "top_negative_aspects": [],
            "merged_positive_aspects": [],
            "merged_negative_aspects": [],
            "categorized_positive": {},
            "categorized_negative": {}
        } 
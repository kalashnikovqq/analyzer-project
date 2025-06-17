from typing import List, Tuple, Set
from .text_preprocessor import TextPreprocessor
from .config import AnalyzerConfig

class AspectMerger:
    
    def __init__(self, preprocessor: TextPreprocessor, config: AnalyzerConfig):
        self.preprocessor = preprocessor
        self.config = config
    
    def merge_similar_aspects(self, aspects: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        if not aspects:
            return []
        
        lemma_aspects = [
            (self.preprocessor.lemmatize_text(aspect.lower()), aspect, count)
            for aspect, count in aspects
        ]
        
        merged_aspects_dict = {}
        used_indices: Set[int] = set()
        
        for i, (lemma_i, aspect_i, count_i) in enumerate(lemma_aspects):
            if i in used_indices:
                continue
            
            merged_aspect_base = aspect_i
            merged_count = count_i
            used_indices.add(i)
            
            for j, (lemma_j, aspect_j, count_j) in enumerate(lemma_aspects):
                if j <= i or j in used_indices:
                    continue
                
                similarity_score = self._calculate_similarity(lemma_i, lemma_j)
                if similarity_score >= self.config.similarity_threshold:
                    if len(aspect_j) > len(merged_aspect_base) * 1.2:
                        merged_aspect_base = aspect_j
                    merged_count += count_j
                    used_indices.add(j)
            
            merged_aspects_dict[merged_aspect_base] = merged_count
        
        result = sorted(merged_aspects_dict.items(), key=lambda x: x[1], reverse=True)
        return result
    
    def _calculate_similarity(self, lemma1: str, lemma2: str) -> float:
        words1 = set(lemma1.split())
        words2 = set(lemma2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        if words1.issubset(words2) or words2.issubset(words1):
            jaccard = max(jaccard, 0.7)
        
        return jaccard 
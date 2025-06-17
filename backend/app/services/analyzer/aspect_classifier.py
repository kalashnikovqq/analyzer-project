from typing import List, Tuple, Optional
from .text_preprocessor import TextPreprocessor

class AspectClassifier:
    
    def __init__(self, preprocessor: TextPreprocessor):
        self.preprocessor = preprocessor
        self._negative_indicators = [
            'плох', 'ужасн', 'страшн', 'некачествен', 'минус', 'дефект', 'поломк', 'сломал',
            'проблем', 'неудоб', 'неработ', 'дорог', 'слаб', 'тяжел', 'громозд', 'большой', 
            'маленьк', 'неудач', 'неприят', 'отврат', 'низк', 'хуже', 'крив', 'брак',
            'скрип', 'скрипит', 'шатает', 'шумит', 'шумн', 'неаккурат', 'некрасив', 'грязн',
            'быстро кончается', 'мало', 'медленн', 'долго', 'нестабильн', 
            'высок цен', 'завышен', 'непонятн', 'сложн', 'путан', 'отвал', 'глюч', 
            'подтормаж', 'недораб', 'сыр', 'недодел', 'бесполез',
            'просвечивает', 'линяет', 'косяк', 'растягивается', 'облезает', 'растрескивается', 
            'садится', 'коробит', 'поблекла', 'растянулась', 'облез', 'растрескался' 
        ]
        
        self._positive_indicators = [
            'хорош', 'отличн', 'прекрасн', 'идеальн', 'качествен', 'удоб', 'приятн', 
            'нравится', 'понравил', 'рад', 'доволен', 'супер', 'шикарн', 'восторг',
            'замечательн', 'классн', 'великолеп', 'превосход', 'крут', 'вкусн',
            'доступн', 'дешев', 'недорог', 'выгодн', 'оправд', 'стоит своих денег',
            'уютн', 'красив', 'аккуратн', 'стильн', 'надежн', 'долговечн', 'прочн',
            'быстр', 'легк', 'тих', 'мощн', 'безопасн', 'безвредн', 'натуральн', 'полезн',
            'эффектив', 'помога', 'работает', 'функционир', 'справля', 'легко',
            'просто', 'интуитивн', 'рекоменд', 'советую', 'покупайте',
            'без косяков', 'без дефектов' 
        ]
    
    def classify_sentiment(self, aspect: str) -> Optional[str]:
        """Определяет тональность аспекта"""
        lemmatized = self.preprocessor.lemmatize_text(aspect.lower())
        
        is_negated = self._check_negation(lemmatized)
        
        has_positive = any(pos in lemmatized for pos in self._positive_indicators)
        has_negative = any(neg in lemmatized for neg in self._negative_indicators)
        
        if is_negated:
            return self._handle_negated_sentiment(lemmatized, has_positive, has_negative)
        
        if has_negative and not has_positive:
            return 'negative'
        elif has_positive and not has_negative:
            return 'positive'
        elif has_negative and has_positive:
            neg_count = sum(1 for neg in self._negative_indicators if neg in lemmatized)
            pos_count = sum(1 for pos in self._positive_indicators if pos in lemmatized)
            return 'negative' if neg_count >= pos_count else 'positive'
        
        return None
    
    def correct_aspects(self, pros: List[Tuple[str, int]], cons: List[Tuple[str, int]]) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
        pros_dict = {aspect: count for aspect, count in pros}
        cons_dict = {aspect: count for aspect, count in cons}
        
        for aspect, count in list(pros_dict.items()):
            sentiment = self.classify_sentiment(aspect)
            if sentiment == 'negative':
                del pros_dict[aspect]
                cons_dict[aspect] = cons_dict.get(aspect, 0) + count
        
        for aspect, count in list(cons_dict.items()):
            sentiment = self.classify_sentiment(aspect)
            if sentiment == 'positive':
                del cons_dict[aspect]
                pros_dict[aspect] = pros_dict.get(aspect, 0) + count
        
        corrected_pros = sorted(pros_dict.items(), key=lambda x: x[1], reverse=True)
        corrected_cons = sorted(cons_dict.items(), key=lambda x: x[1], reverse=True)
        
        return corrected_pros, corrected_cons
    
    def _check_negation(self, lemmatized: str) -> bool:
        return lemmatized.startswith('не ') or lemmatized.startswith('без ')
    
    def _handle_negated_sentiment(self, lemmatized: str, has_positive: bool, has_negative: bool) -> Optional[str]:
        if lemmatized.startswith('не '):
            text_after_negation = lemmatized[3:]
            pos_in_remainder = any(pos in text_after_negation for pos in self._positive_indicators)
            neg_in_remainder = any(neg in text_after_negation for neg in self._negative_indicators)
            
            if neg_in_remainder and not pos_in_remainder:  # "не плохой"
                return 'positive'
            elif pos_in_remainder and not neg_in_remainder:  # "не хороший"
                return 'negative'
        
        elif lemmatized.startswith('без '):
            text_after_negation = lemmatized[4:]
            if any(neg in text_after_negation for neg in self._negative_indicators):  # "без дефектов"
                return 'positive'
        
        return None 
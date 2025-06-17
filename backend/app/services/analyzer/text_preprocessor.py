import re
import string
import unicodedata
from typing import Dict
import pymorphy2

class TextPreprocessor:
    def __init__(self):
        self.morph = pymorphy2.MorphAnalyzer()
        self._russian_endings = {
            'отличн': 'ый', 'хорош': 'ий', 'плох': 'ой', 'красив': 'ый',
            'наклей': 'ка', 'размер': '', 'приятн': 'ый', 'интересн': 'ый',
            'достоинств': 'а', 'красн': 'ый', 'черн': 'ый', 'син': 'ий',
            'качеств': 'о', 'удобств': 'о', 'выдерж': 'ка', 'раз': 'мер',
            'вс': 'ё', 'больш': 'ой', 'маленьк': 'ий', 'удобн': 'ый'
        }
    
    def preprocess_review(self, review: str) -> str:
        if not review or not isinstance(review, str):
            return ""
        
        review = unicodedata.normalize('NFKC', review).lower()
        review = self._remove_emojis(review)
        review = self._decode_html_entities(review)
        review = self._normalize_whitespace(review)
        review = self._normalize_punctuation(review)
        
        return review.strip(string.punctuation + ' ')
    
    def lemmatize_text(self, text: str) -> str:
        if not text:
            return ""
        
        words = text.split()
        lemmatized_words = []
        
        for word in words:
            clean_word = word.strip(string.punctuation)
            if clean_word:
                parsed = self.morph.parse(clean_word)[0]
                lemmatized_words.append(parsed.normal_form)
        
        return ' '.join(lemmatized_words)
    
    def clean_aspect(self, aspect: str) -> str:
        if not aspect:
            return ""
        
        if aspect in self._russian_endings:
            aspect += self._russian_endings[aspect]
        
        aspect = aspect.strip()
        aspect = re.sub(r'\s+', ' ', aspect)
        aspect = re.sub(r'([!?.,:;])\1+', r'\1', aspect)
        aspect = aspect.strip(string.punctuation + ' ')
        
        return aspect
    
    def _remove_emojis(self, text: str) -> str:
        emoji_pattern = re.compile(
            "["
            u"\U0001F000-\U0001F9FF"  
            u"\U00002700-\U000027BF"  
            u"\U0001F600-\U0001F64F"  
            u"\U0001F300-\U0001F5FF"  
            u"\U0001F680-\U0001F6FF"  
            u"\U0001F700-\U0001F77F"  
            u"\U0001F780-\U0001F7FF"  
            u"\U0001F800-\U0001F8FF"  
            u"\U0001F900-\U0001F9FF"  
            u"\U00002702-\U000027B0"  
            u"\U000024C2-\U0001F251"  
            u"\U0001f926-\U0001f937"  
            u"\U0001F1E0-\U0001F1FF"  
            u"\u200d"                 
            u"\u2640-\u2642"          
            u"\u2600-\u2B55"          
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\u3030"
            u"\ufe0f"                 
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.sub(' ', text)
    
    def _decode_html_entities(self, text: str) -> str:
        replacements = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>', 
            '&quot;': '"', '&#39;': "'"
        }
        for entity, char in replacements.items():
            text = text.replace(entity, char)
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r'[\s\t\n\r]+', ' ', text)
    
    def _normalize_punctuation(self, text: str) -> str:
        text = re.sub(r'([!?,.;:])\1+', r'\1', text)  
        text = re.sub(r'([!?,.;:])([^\s])', r'\1 \2', text)  
        return text 
import torch
import string
from typing import List, Tuple, Optional
from .model_loader import ModelLoader
from .text_preprocessor import TextPreprocessor
from .config import AnalyzerConfig

class AspectExtractor:
    
    def __init__(self, model_loader: ModelLoader, preprocessor: TextPreprocessor, config: AnalyzerConfig):
        self.model_loader = model_loader
        self.preprocessor = preprocessor
        self.config = config
        self.model, self.tokenizer, self.device, self.id2label = model_loader.load_model()
    
    def extract_aspects(self, text: str) -> Tuple[List[str], List[str]]:
        if not text.strip():
            return [], []
        
        if len(text) > self.config.max_len * 2:
            return self._extract_with_sliding_window(text)
        
        if len(text) > self.config.max_text_length:
            text = text[:self.config.max_text_length]
        
        predictions, confidences, offsets = self._get_model_predictions(text)
        return self._process_bio_predictions(text, predictions, confidences, offsets)
    
    def _get_model_predictions(self, text: str) -> Tuple[List[str], List[float], List[tuple]]:
        inputs = self.tokenizer(
            text,
            max_length=self.config.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt',
            return_offsets_mapping=True
        )
        
        offset_mapping = inputs.pop('offset_mapping').numpy()[0]
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=2)
            confidence, predictions = torch.max(probabilities, dim=2)
        
        predicted_labels = [self.id2label[label_id.item()] for label_id in predictions[0]]
        confidences = confidence[0].cpu().numpy()
        
        filtered_predictions = []
        filtered_confidences = []
        filtered_offsets = []
        
        for i, (pred, conf, offset) in enumerate(zip(predicted_labels, confidences, offset_mapping)):
            if offset[0] == 0 and offset[1] == 0:  
                continue
            if attention_mask[0][i].item() == 0:  
                continue
            
            filtered_predictions.append(pred)
            filtered_confidences.append(conf)
            filtered_offsets.append(offset)
        
        return filtered_predictions, filtered_confidences, filtered_offsets
    
    def _process_bio_predictions(self, text: str, predictions: List[str], 
                                confidences: List[float], offsets: List[tuple]) -> Tuple[List[str], List[str]]:
        positive_aspects = []
        negative_aspects = []
        
        current_tokens = []
        current_offsets = []
        current_confidences = []
        current_type = None
        
        for pred, conf, offset in zip(predictions, confidences, offsets):
            if pred.startswith('B-'):
                self._finalize_aspect(text, current_offsets, current_confidences, 
                                    current_type, positive_aspects, negative_aspects)
                
                current_tokens = [pred]
                current_offsets = [offset]
                current_confidences = [conf]
                current_type = 'positive' if pred == 'B-positive' else 'negative'
            
            elif pred.startswith('I-') and current_tokens:
                expected_type = 'positive' if pred == 'I-positive' else 'negative'
                if current_type == expected_type:
                    current_tokens.append(pred)
                    current_offsets.append(offset)
                    current_confidences.append(conf)
                else:
                    self._finalize_aspect(text, current_offsets, current_confidences, 
                                        current_type, positive_aspects, negative_aspects)
                    current_tokens = []
                    current_offsets = []
                    current_confidences = []
                    current_type = None
            
            elif pred == 'O':
                self._finalize_aspect(text, current_offsets, current_confidences, 
                                    current_type, positive_aspects, negative_aspects)
                current_tokens = []
                current_offsets = []
                current_confidences = []
                current_type = None
        
        self._finalize_aspect(text, current_offsets, current_confidences, 
                            current_type, positive_aspects, negative_aspects)
        
        return sorted(list(set(positive_aspects))), sorted(list(set(negative_aspects)))
    
    def _finalize_aspect(self, text: str, offsets: List[tuple], confidences: List[float], 
                        aspect_type: Optional[str], positive_aspects: List[str], 
                        negative_aspects: List[str]) -> None:
        if not offsets or not confidences or not aspect_type:
            return
        
        start_idx = offsets[0][0]
        end_idx = offsets[-1][1]
        raw_text = text[start_idx:end_idx]
        cleaned_text = self.preprocessor.clean_aspect(raw_text)
        
        if self._is_valid_aspect(cleaned_text, confidences):
            if aspect_type == 'positive':
                positive_aspects.append(cleaned_text)
            elif aspect_type == 'negative':
                negative_aspects.append(cleaned_text)
    
    def _is_valid_aspect(self, aspect: str, confidences: List[float]) -> bool:
        if len(aspect) < self.config.min_aspect_length:
            return False
        
        if not any(c.isalpha() for c in aspect):
            return False
        
        if aspect.strip() in string.punctuation:
            return False
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        if avg_confidence < self.config.confidence_threshold:
            return False
        
        stopwords = {'и', 'или', 'но', 'а', 'да', 'в', 'на', 'по', 'к', 'у', 'из', 'с', 'о', 'от', 'для', 'при', 'за'}
        words = aspect.lower().split()
        if all(word in stopwords for word in words):
            return False
        
        return True
    
    def _extract_with_sliding_window(self, text: str) -> Tuple[List[str], List[str]]:
        all_positive = []
        all_negative = []
        
        step_size = self.config.max_len // 2
        
        for start in range(0, len(text), step_size):
            window_text = text[start:start + self.config.max_len]
            if len(window_text.strip()) < 10:
                continue
            
            pos_aspects, neg_aspects = self.extract_aspects(window_text)
            all_positive.extend(pos_aspects)
            all_negative.extend(neg_aspects)
        
        return sorted(list(set(all_positive))), sorted(list(set(all_negative))) 
import logging
import torch
from typing import Tuple, Dict
from transformers import XLMRobertaTokenizerFast, XLMRobertaForTokenClassification
from .config import AnalyzerConfig

logger = logging.getLogger('review_analyzer.model_loader')

class ModelLoader:
    
    def __init__(self, config: AnalyzerConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.device = None
        self.id2label = None
    
    def load_model(self) -> Tuple[object, object, torch.device, Dict[int, str]]:
        if self.model is not None:
            return self.model, self.tokenizer, self.device, self.id2label
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        try:
            self.tokenizer = XLMRobertaTokenizerFast.from_pretrained(self.config.model_path)
            self.model = XLMRobertaForTokenClassification.from_pretrained(self.config.model_path)
            
            self.model.to(self.device)
            self.model.eval()
            
            self.id2label = self._adapt_labels(self.model.config.id2label)
            
            return self.model, self.tokenizer, self.device, self.id2label
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {e}")
            raise RuntimeError(f"Не удалось загрузить модель из {self.config.model_path}") from e
    
    def _adapt_labels(self, original_labels: Dict[int, str]) -> Dict[int, str]:
        adapted_labels = {}
        
        for label_id, label in original_labels.items():
            if label == 'B-POS':
                adapted_labels[label_id] = 'B-positive'
            elif label == 'I-POS':
                adapted_labels[label_id] = 'I-positive'
            elif label == 'B-NEG':
                adapted_labels[label_id] = 'B-negative'
            elif label == 'I-NEG':
                adapted_labels[label_id] = 'I-negative'
            else:
                adapted_labels[label_id] = label
        
        required_labels = {'B-positive', 'I-positive', 'B-negative', 'I-negative', 'O'}
        available_labels = set(adapted_labels.values())
        
        if not required_labels.issubset(available_labels):
            logger.warning(f"Не все требуемые метки доступны: {required_labels - available_labels}")
        
        return adapted_labels
    
    def get_device(self) -> torch.device:
        if self.device is None:
            self.load_model()
        return self.device 
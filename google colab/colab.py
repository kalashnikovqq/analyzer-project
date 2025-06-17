# !pip install torch==2.0.1 --extra-index-url https://download.pytorch.org/whl/cu118 && \
# pip install transformers==4.30.2 tokenizers scikit-learn==1.2.2 seqeval==1.2.2 matplotlib==3.7.1 tensorboard==2.13.0 tqdm==4.65.0 numpy==1.25.0


import os
import random
import string
import logging
import re
from collections import Counter
from typing import List, Tuple, Dict

import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from transformers import (
    XLMRobertaForTokenClassification,
    XLMRobertaTokenizerFast,
    AdamW,
    get_linear_schedule_with_warmup,
    DataCollatorForTokenClassification,
    AutoConfig
)
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score
from torch.nn import CrossEntropyLoss
from torch.utils.tensorboard import SummaryWriter
from torch.cuda.amp import GradScaler, autocast
from tqdm import tqdm
import torch.nn as nn
import torch
import numpy as np


class Config:
    SEED = 42
    MAX_LEN = 192  
    BATCH_SIZE = 12
    EPOCHS = 35
    GRADIENT_ACCUMULATION_STEPS = 4  
    LEARNING_RATE = 3e-5
    WEIGHT_DECAY = 0.01
    WARMUP_RATIO = 0.1
    EPS = 1e-8
    EARLY_STOP_PATIENCE = 5
    MODEL_NAME = 'xlm-roberta-large'
    
    USE_FOCAL_LOSS = False
    FOCAL_LOSS_GAMMA = 2.0
    
    BIO_TAGS_FILE = 'dataset/bio_tags.txt'
    BEST_MODEL_DIR = 'best_model'
    SAVED_MODEL_DIR = 'saved_model'
    NUM_WORKERS = 2
    MAX_GRAD_NORM = 1.0
    USE_STRATIFIED_SPLIT = True


ALL_LABELS = ['O', 'B-POS', 'I-POS', 'B-NEG', 'I-NEG']


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def set_seed(seed: int = Config.SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_bio_tags(file_path: str) -> List[Tuple[List[str], List[str]]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл '{file_path}' не найден.")
    
    reviews = []
    tokens, labels = [], []
    
    # Парсим файл с BIO-разметкой (токен\tметка)
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):  # начало нового отзыва
                if tokens and labels:
                    reviews.append((tokens, labels))
                    tokens, labels = [], []
                continue
            if line:
                parts = line.split()
                if len(parts) == 2:
                    token, label = parts
                    tokens.append(token)
                    labels.append(label)
        
        if tokens and labels:
            reviews.append((tokens, labels))
    
    return reviews


def preprocess_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(string.punctuation + ' ')
    text = re.sub(r'([!?,;.])\1+', r'\1', text)
    return text


def clean_text_for_analysis(text: str) -> str:
    text = preprocess_text(text)
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"
                           u"\U0001F300-\U0001F5FF"
                           u"\U0001F680-\U0001F6FF"
                           u"\U0001F1E0-\U0001F1FF"
                           "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'\b\d+\b', '<NUM>', text)
    return text


def dominant_label(labels: List[str]) -> str:
    classes = [l.split('-', 1)[-1] for l in labels if l.startswith(('B-', 'I-'))]
    if classes:
        return Counter(classes).most_common(1)[0][0]
    return 'O'


def create_label_mapping(all_labels: List[str]) -> Tuple[Dict[str, int], Dict[int, str]]:
    unique_labels = sorted(set(all_labels))
    label2id = {label: i for i, label in enumerate(unique_labels)}
    id2label = {i: label for label, i in label2id.items()}
    return label2id, id2label


def stratified_split(reviews: List[Tuple[List[str], List[str]]], test_size=0.2, random_state=None):
    doc_labels = [dominant_label(labels) for _, labels in reviews]
    label_indices = {label: [] for label in set(doc_labels)}
    
    for i, label in enumerate(doc_labels):
        label_indices[label].append(i)
    
    train_indices = []
    val_indices = []
    
    for label, indices in label_indices.items():
        split_point = int(len(indices) * (1 - test_size))
        if random_state is not None:
            random.Random(random_state).shuffle(indices)
        
        train_indices.extend(indices[:split_point])
        val_indices.extend(indices[split_point:])
    
    train_reviews = [reviews[i] for i in train_indices]
    val_reviews = [reviews[i] for i in val_indices]
    
    return train_reviews, val_reviews


class ReviewsDataset(Dataset):
    def __init__(self, reviews: List[Tuple[List[str], List[str]]], 
                 tokenizer: XLMRobertaTokenizerFast, label2id: Dict[str, int], max_len: int):
        self.reviews = reviews
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_len = max_len

    def __len__(self):
        return len(self.reviews)

    def __getitem__(self, idx: int):
        tokens, labels = self.reviews[idx]
        
        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_len,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].squeeze()
        attention_mask = encoding['attention_mask'].squeeze()
        word_ids = encoding.word_ids(batch_index=0)
        
        label_ids = []
        previous_word_idx = None
        
        for word_idx in word_ids:
            if word_idx is None:  # специальные токены [CLS], [SEP]
                label_ids.append(-100)
            elif word_idx != previous_word_idx:  # первый subword токен
                label_ids.append(self.label2id.get(labels[word_idx], self.label2id['O']))
            else:  # остальные subword токены
                label_ids.append(-100)
            previous_word_idx = word_idx
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': torch.tensor(label_ids, dtype=torch.long)
        }


class FocalLoss(nn.Module):
    def __init__(self, gamma=2.0, weight=None, reduction='mean', ignore_index=-100):
        super(FocalLoss, self).__init__()
        self.gamma = gamma
        self.weight = weight
        self.reduction = reduction
        self.ignore_index = ignore_index
        self.ce_loss = CrossEntropyLoss(weight=weight, reduction='none', ignore_index=ignore_index)

    def forward(self, inputs, targets):
        ce_loss = self.ce_loss(inputs, targets)
        pt = torch.exp(-ce_loss)
        loss = (1 - pt) ** self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss


class AspectExtractorTrainer:
    def __init__(self, config=Config):
        self.config = config
        self.logger = setup_logging()
        self.device = self._setup_device()
        self.model = None
        self.tokenizer = None
        self.label2id = None
        self.id2label = None
        
    def _setup_device(self):
        if torch.cuda.is_available():
            device = torch.device("cuda")
            torch.cuda.empty_cache()
            torch.backends.cudnn.benchmark = True
            self.logger.info(f"Используется GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            self.logger.info("Используется CPU")
        return device
    
    def _analyze_data(self, reviews):
        label_counts = {label: 0 for label in ALL_LABELS}
        for _, labels in reviews:
            for label in labels:
                if label in label_counts:
                    label_counts[label] += 1
        
        doc_labels = [dominant_label(labels) for _, labels in reviews]
        doc_counts = Counter(doc_labels)
        
        total_tokens = sum(label_counts.values())
        self.logger.info(f"Всего токенов: {total_tokens}")
        for label, count in label_counts.items():
            percentage = (count / total_tokens) * 100 if total_tokens > 0 else 0
            self.logger.info(f"{label}: {count} ({percentage:.2f}%)")
        
        return label_counts, doc_counts
    
    def _calculate_class_weights(self, label_counts):
        total = sum(label_counts.values())
        weights = {label: total / count if count > 0 else 1.0 for label, count in label_counts.items()}
        return torch.tensor([weights[k] for k in sorted(weights.keys())], dtype=torch.float)
    
    def _setup_model_and_tokenizer(self):
        self.tokenizer = XLMRobertaTokenizerFast.from_pretrained(self.config.MODEL_NAME, use_fast=True)
        
        model_config = AutoConfig.from_pretrained(
            self.config.MODEL_NAME,
            num_labels=len(self.label2id),
            id2label=self.id2label,
            label2id=self.label2id,
        )
        
        self.model = XLMRobertaForTokenClassification.from_pretrained(
            self.config.MODEL_NAME,
            config=model_config,
            from_tf=False,
            ignore_mismatched_sizes=True
        ).to(self.device)
    
    def _create_data_loaders(self, train_reviews, val_reviews):
        train_dataset = ReviewsDataset(train_reviews, self.tokenizer, self.label2id, self.config.MAX_LEN)
        val_dataset = ReviewsDataset(val_reviews, self.tokenizer, self.label2id, self.config.MAX_LEN)
        
        data_collator = DataCollatorForTokenClassification(tokenizer=self.tokenizer)
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.BATCH_SIZE,
            shuffle=True,
            collate_fn=data_collator,
            num_workers=self.config.NUM_WORKERS,
            pin_memory=True
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.BATCH_SIZE * 2,
            shuffle=False,
            collate_fn=data_collator,
            num_workers=self.config.NUM_WORKERS,
            pin_memory=True
        )
        
        return train_loader, val_loader
    
    def _setup_training_components(self, train_loader, label_counts):
        optimizer = AdamW(
            self.model.parameters(),
            lr=self.config.LEARNING_RATE,
            eps=self.config.EPS,
            weight_decay=self.config.WEIGHT_DECAY
        )
        
        total_steps = len(train_loader) * self.config.EPOCHS // self.config.GRADIENT_ACCUMULATION_STEPS
        warmup_steps = int(total_steps * self.config.WARMUP_RATIO)
        
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )
        
        scaler = GradScaler()
        
        if self.config.USE_FOCAL_LOSS:
            loss_fn = FocalLoss(gamma=self.config.FOCAL_LOSS_GAMMA, ignore_index=-100)
        else:
            loss_fn = CrossEntropyLoss(ignore_index=-100)
        
        return optimizer, scheduler, scaler, loss_fn
    
    def _train_epoch(self, model, data_loader, optimizer, scheduler, loss_fn, writer, epoch, scaler):
        model.train()
        losses = []
        progress_bar = tqdm(data_loader, desc=f"Эпоха {epoch+1} [ОБУЧЕНИЕ]")
        
        for step, batch in enumerate(progress_bar):
            batch = {k: v.to(self.device) for k, v in batch.items()}
            labels = batch['labels']
            
            with autocast():  
                outputs = model(**{k: v for k, v in batch.items() if k != 'labels'})
                logits = outputs.logits
                loss = loss_fn(logits.view(-1, logits.shape[-1]), labels.view(-1))
                loss = loss / self.config.GRADIENT_ACCUMULATION_STEPS
            
            scaler.scale(loss).backward()
            
            if (step + 1) % self.config.GRADIENT_ACCUMULATION_STEPS == 0 or step == len(data_loader) - 1:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), self.config.MAX_GRAD_NORM)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()
            
            losses.append(loss.item() * self.config.GRADIENT_ACCUMULATION_STEPS)
            progress_bar.set_postfix({'loss': sum(losses) / len(losses)})
        
        avg_loss = sum(losses) / len(losses)
        writer.add_scalar('training_loss', avg_loss, epoch)
        return avg_loss
    
    def _eval_model(self, model, data_loader, writer, epoch):
        model.eval()
        val_loss = 0
        val_steps = 0
        preds_list = []
        labels_list = []
        
        val_loss_fn = CrossEntropyLoss(ignore_index=-100)
        progress_bar = tqdm(data_loader, desc=f"Эпоха {epoch+1} [ВАЛИДАЦИЯ]")
        
        with torch.no_grad():
            for batch in progress_bar:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                labels = batch['labels']
                
                outputs = model(**{k: v for k, v in batch.items() if k != 'labels'})
                logits = outputs.logits
                
                loss = val_loss_fn(logits.view(-1, logits.shape[-1]), labels.view(-1))
                val_loss += loss.item()
                val_steps += 1
                
                batch_preds = torch.argmax(logits, dim=2)
                
                for i in range(batch['input_ids'].shape[0]):
                    preds = []
                    true_labels = []
                    
                    for j in range(batch['attention_mask'][i].sum().item()):
                        if batch['labels'][i, j] != -100:
                            token_pred = self.id2label[batch_preds[i, j].item()]
                            token_true = self.id2label[batch['labels'][i, j].item()]
                            preds.append(token_pred)
                            true_labels.append(token_true)
                    
                    if preds and true_labels:
                        preds_list.append(preds)
                        labels_list.append(true_labels)
        
        avg_val_loss = val_loss / val_steps if val_steps > 0 else 0
        
        if preds_list and labels_list:
            val_f1 = f1_score(labels_list, preds_list)
            val_precision = precision_score(labels_list, preds_list)
            val_recall = recall_score(labels_list, preds_list)
            report = classification_report(labels_list, preds_list, digits=4)
            
            writer.add_scalar('validation_loss', avg_val_loss, epoch)
            writer.add_scalar('validation_f1', val_f1, epoch)
            writer.add_scalar('validation_precision', val_precision, epoch)
            writer.add_scalar('validation_recall', val_recall, epoch)
            
            return avg_val_loss, val_f1, val_precision, val_recall, report
        else:
            return avg_val_loss, 0, 0, 0, "Нет данных для валидации"
    
    def plot_metrics(self, train_losses, val_losses, val_f1_scores, val_precision_scores, val_recall_scores):
        epochs_range = range(1, len(train_losses) + 1)
        
        plt.figure(figsize=(20, 10))
        
        plt.subplot(2, 2, 1)
        plt.plot(epochs_range, train_losses, marker='o', label='Потеря при обучении')
        plt.plot(epochs_range, val_losses, marker='o', label='Потеря при валидации')
        plt.xlabel('Эпоха')
        plt.ylabel('Потеря')
        plt.legend()
        plt.title('Потеря')
        plt.grid(True)
        
        plt.subplot(2, 2, 2)
        plt.plot(epochs_range, val_f1_scores, marker='o', label='F1 при валидации', color='green')
        plt.xlabel('Эпоха')
        plt.ylabel('F1-метрика')
        plt.legend()
        plt.title('F1-метрика')
        plt.grid(True)
        
        plt.subplot(2, 2, 3)
        plt.plot(epochs_range, val_precision_scores, marker='o', label='Точность при валидации', color='orange')
        plt.xlabel('Эпоха')
        plt.ylabel('Точность')
        plt.legend()
        plt.title('Точность')
        plt.grid(True)
        
        plt.subplot(2, 2, 4)
        plt.plot(epochs_range, val_recall_scores, marker='o', label='Полнота при валидации', color='red')
        plt.xlabel('Эпоха')
        plt.ylabel('Полнота')
        plt.legend()
        plt.title('Полнота')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def train(self):
        set_seed(self.config.SEED)
        
        self.logger.info("Загрузка данных...")
        reviews = load_bio_tags(self.config.BIO_TAGS_FILE)
        
        self.logger.info("Анализ данных...")
        label_counts, doc_counts = self._analyze_data(reviews)
        
        self.label2id, self.id2label = create_label_mapping(ALL_LABELS)
        
        self.logger.info("Разделение данных...")
        if self.config.USE_STRATIFIED_SPLIT:
            train_reviews, val_reviews = stratified_split(reviews, test_size=0.2, random_state=self.config.SEED)
        else:
            train_reviews, val_reviews = train_test_split(reviews, test_size=0.2, random_state=self.config.SEED)
        
        self.logger.info(f"Обучающих примеров: {len(train_reviews)}, Валидационных: {len(val_reviews)}")
        
        self.logger.info("Инициализация модели...")
        self._setup_model_and_tokenizer()
        
        train_loader, val_loader = self._create_data_loaders(train_reviews, val_reviews)
        optimizer, scheduler, scaler, loss_fn = self._setup_training_components(train_loader, label_counts)
        
        writer = SummaryWriter()
        
        best_val_f1 = 0.0
        epochs_no_improve = 0
        train_losses = []
        val_losses = []
        val_f1_scores = []
        val_precision_scores = []
        val_recall_scores = []
        
        self.logger.info("Начинаем обучение...")
        for epoch in range(self.config.EPOCHS):
            if epochs_no_improve >= self.config.EARLY_STOP_PATIENCE:
                self.logger.info("Ранняя остановка")
                break
            
            train_loss = self._train_epoch(
                self.model, train_loader, optimizer, scheduler, loss_fn, writer, epoch, scaler
            )
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            val_loss, val_f1, val_precision, val_recall, val_report = self._eval_model(
                self.model, val_loader, writer, epoch
            )
            
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            val_f1_scores.append(val_f1)
            val_precision_scores.append(val_precision)
            val_recall_scores.append(val_recall)
            
            print(f"\nЭпоха {epoch+1}:")
            print(f"Потеря обучения: {train_loss:.4f}")
            print(f"Потеря валидации: {val_loss:.4f}")
            print(f"F1: {val_f1:.4f}, Precision: {val_precision:.4f}, Recall: {val_recall:.4f}")
            print(val_report)
            
            if val_f1 > best_val_f1 + 0.001:
                best_val_f1 = val_f1
                epochs_no_improve = 0
                os.makedirs(self.config.BEST_MODEL_DIR, exist_ok=True)
                self.model.save_pretrained(self.config.BEST_MODEL_DIR)
                self.tokenizer.save_pretrained(self.config.BEST_MODEL_DIR)
                self.logger.info("Лучшая модель сохранена")
            else:
                epochs_no_improve += 1
        
        writer.close()
        self.plot_metrics(train_losses, val_losses, val_f1_scores, val_precision_scores, val_recall_scores)
        
        if os.path.exists(self.config.BEST_MODEL_DIR):
            self.model = XLMRobertaForTokenClassification.from_pretrained(self.config.BEST_MODEL_DIR).to(self.device)
            self.tokenizer = XLMRobertaTokenizerFast.from_pretrained(self.config.BEST_MODEL_DIR)
        
        os.makedirs(self.config.SAVED_MODEL_DIR, exist_ok=True)
        self.model.save_pretrained(self.config.SAVED_MODEL_DIR)
        self.tokenizer.save_pretrained(self.config.SAVED_MODEL_DIR)
        
        return self.model, self.tokenizer, self.device, self.id2label
    
    def predict(self, text: str) -> List[Tuple[str, str]]:
        text = clean_text_for_analysis(text)
        self.model.eval()
        
        encoded = self.tokenizer.encode_plus(
            text,
            max_length=self.config.MAX_LEN,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoded['input_ids'].to(self.device)
        attention_mask = encoded['attention_mask'].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            predictions = torch.argmax(outputs.logits, dim=2)
        
        word_ids = encoded.word_ids(batch_index=0)
        previous_word_id = None
        current_word = []
        current_label = None
        words_labels = []
        
        for i, word_id in enumerate(word_ids):
            if word_id is None or not attention_mask[0, i]:
                continue
                
            pred_id = predictions[0, i].item()
            label = self.id2label.get(pred_id, 'O')
            token = self.tokenizer.convert_ids_to_tokens(input_ids[0, i].item())
            
            clean_token = token.lstrip('▁ ') 
            
            if word_id != previous_word_id:
                if current_word:
                    word = ''.join(current_word).strip()
                    words_labels.append((word, current_label))
                current_word = [clean_token]
                current_label = label
            else:
                current_word.append(clean_token)
                if label.startswith('B-'):
                    current_label = label
                elif label.startswith('I-') and current_label == 'O':
                    current_label = label
            
            previous_word_id = word_id
        
        if current_word:
            word = ''.join(current_word).strip()
            words_labels.append((word, current_label))
        
        return words_labels
    
    def predict_and_split(self, text: str):
        reconstruction = self.predict(text)
        
        pros = []
        cons = []
        current_aspect = None
        current_tokens = []
        
        for token, label in reconstruction:
            token = token.strip(string.punctuation + ' ')
            if not token:
                continue
            
            if label.startswith('B-POS'):
                if current_aspect and current_tokens:
                    if current_aspect == 'POS':
                        pros.append(' '.join(current_tokens))
                    elif current_aspect == 'NEG':
                        cons.append(' '.join(current_tokens))
                current_aspect = 'POS'
                current_tokens = [token]
            elif label.startswith('I-POS') and current_aspect == 'POS':
                current_tokens.append(token)
            elif label.startswith('B-NEG'):
                if current_aspect and current_tokens:
                    if current_aspect == 'POS':
                        pros.append(' '.join(current_tokens))
                    elif current_aspect == 'NEG':
                        cons.append(' '.join(current_tokens))
                current_aspect = 'NEG'
                current_tokens = [token]
            elif label.startswith('I-NEG') and current_aspect == 'NEG':
                current_tokens.append(token)
            else:  
                if current_aspect and current_tokens:
                    if current_aspect == 'POS':
                        pros.append(' '.join(current_tokens))
                    elif current_aspect == 'NEG':
                        cons.append(' '.join(current_tokens))
                current_aspect = None
                current_tokens = []
        
        if current_aspect and current_tokens:
            if current_aspect == 'POS':
                pros.append(' '.join(current_tokens))
            elif current_aspect == 'NEG':
                cons.append(' '.join(current_tokens))
        
        return list(set(pros)), list(set(cons))


def main():
    trainer = AspectExtractorTrainer()
    model, tokenizer, device, id2label = trainer.train()
    
    example_review = "Футболка отличного качества, очень понравилась."
    pros, cons = trainer.predict_and_split(example_review)
    print(f"\nПример предсказания:")
    print(f"Отзыв: {example_review}")
    print(f"Плюсы: {pros}")
    print(f"Минусы: {cons}")


if __name__ == "__main__":
    main() 
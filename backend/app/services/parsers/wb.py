import logging
import re
import sys
import os
import time
import json
from typing import List, Dict, Any, Optional, Union
import random
from pathlib import Path

from app.core.config import settings

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from pydantic import BaseModel

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("WildberriesParser")

class Review(BaseModel):
    id: str
    text: str = ""
    pros: str = ""
    cons: str = ""
    userName: str = ""
    productValuation: int = 0
    createdDate: str = ""
    photos: List[Dict[str, str]] = []
    votes: Dict[str, int] = {}

class ReviewsResponse(BaseModel):
    feedbacks: List[Review]

def extract_reviews_text(reviews: List[Dict[str, Any]]) -> List[str]:
    result = []
    for review in reviews:
        try:
            text_parts = []
            if review.get("text"):
                text_parts.append(review["text"])
            if review.get("pros"):
                text_parts.append(f"Достоинства: {review['pros']}")
            if review.get("cons"):
                text_parts.append(f"Недостатки: {review['cons']}")
            
            if text_parts:
                result.append(" ".join(text_parts))
        except Exception:
            continue
    
    return result

class WildberriesParser:
    
    DEFAULT_TIMEOUT = 5  
    MAX_RETRIES = 2      
    RETRY_DELAY = 1      
    FEEDBACK_DOMAINS = ["feedbacks1.wb.ru", "feedbacks2.wb.ru"] 
    API_VERSIONS = ["v1", "v2"]  
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Origin": "https://www.wildberries.ru",
            "Referer": "https://www.wildberries.ru/",
        }
        
    def _get_reviews_with_params(self, url: str, params: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT, retries: int = MAX_RETRIES, version: str = "v1") -> List[Review]:
        attempt = 0
        delay = self.RETRY_DELAY

        while attempt <= retries:
            try:
                response = requests.get(url=url, headers=self.headers, params=params, timeout=timeout)

                if response.status_code == 429:
                    attempt += 1
                    wait_time = delay * (2 ** attempt)
                    time.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    if 400 <= response.status_code < 500 and response.status_code != 429:
                         return []
                    if attempt < retries:
                        attempt += 1
                        wait_time = delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    else:
                        return []

                if not response.content:
                     return []
                
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return []

                if not data:
                    return []

                feedbacks_key = None
                
                if "feedbacks" in data and isinstance(data["feedbacks"], list) and data["feedbacks"]:
                    feedbacks_key = "feedbacks"
                elif isinstance(data, list):
                    feedbacks_key = None
                else:
                    potential_keys = ["comments", "reviews", "data", "items"]
                    for key in potential_keys:
                        if key in data and isinstance(data[key], list) and data[key]:
                            feedbacks_key = key
                            break
                    
                    if not feedbacks_key:
                        if "feedbackCount" in data and data["feedbackCount"] > 0 and "feedbacks" in data:
                            if "/api/v1/feedbacks/" in url:
                                alternative_url = url.replace("/api/v1/feedbacks/", "/feedbacks/v1/")
                                return self._get_reviews_with_params(alternative_url, params, timeout, retries, version)
                        
                        for key in ["data", "result", "results", "content", "response"]:
                            if key in data and isinstance(data[key], dict):
                                for subkey in ["feedbacks", "comments", "reviews", "items"]:
                                    if subkey in data[key] and isinstance(data[key][subkey], list) and data[key][subkey]:
                                        feedbacks_key = f"{key}.{subkey}"
                                        break
                                if feedbacks_key:
                                    break
                        
                        if not feedbacks_key and isinstance(data, list):
                            feedbacks_key = None
                        elif not feedbacks_key:
                            return []

                reviews_raw = []
                if feedbacks_key is None:
                    reviews_raw = data
                elif "." in str(feedbacks_key):
                    keys = feedbacks_key.split(".")
                    temp_data = data
                    for key in keys:
                        temp_data = temp_data.get(key, [])
                    reviews_raw = temp_data
                else:
                    reviews_raw = data.get(feedbacks_key, [])

                if not reviews_raw:
                    return []

                reviews = []
                for review_data in reviews_raw:
                    try:
                        review = Review(**review_data)
                        reviews.append(review)
                    except Exception:
                        continue

                return reviews

            except (ConnectionError, Timeout, RequestException):
                if attempt < retries:
                    attempt += 1
                    time.sleep(delay * (2 ** attempt))
                    continue
                else:
                    break
            except Exception:
                break

        return []

    def get_all_reviews(self, imt_id: Union[int, str], max_reviews_count: int = 1000, timeout: int = DEFAULT_TIMEOUT, retries: int = MAX_RETRIES) -> List[Review]:

        imt_id_str = str(imt_id)

        all_reviews_collected = []
        collected_review_ids = set()
        
        main_urls = [
            f"https://feedbacks1.wb.ru/feedbacks/v1/{imt_id_str}",
            f"https://feedbacks2.wb.ru/feedbacks/v1/{imt_id_str}"
        ]
        
        for main_url in main_urls:
            reviews = self._get_reviews_with_params(main_url, params={}, timeout=timeout, retries=retries, version="v1")
            
            if reviews:
                newly_added = 0
                for review in reviews:
                    if review.id not in collected_review_ids:
                        all_reviews_collected.append(review)
                        collected_review_ids.add(review.id)
                        newly_added += 1
                
                
                if len(all_reviews_collected) >= max_reviews_count:
                    break
            else:
                logger.warning(f"Отзывы не найдены с {main_url}")
        
        if len(all_reviews_collected) < max_reviews_count:
            
            for domain in self.FEEDBACK_DOMAINS:
                for version in self.API_VERSIONS:
                    if len(all_reviews_collected) >= max_reviews_count:
                        break
                    
                    alternative_urls = [
                        f"https://{domain}/api/{version}/feedbacks/{imt_id_str}"
                    ]
                    
                    for url in alternative_urls:
                        if url in main_urls:
                            continue  
                        
                        batch_reviews = self._get_reviews_with_params(
                            url, params={}, timeout=timeout, retries=retries, version=version
                        )
                        
                        newly_added = 0
                        for review in batch_reviews:
                            if review.id not in collected_review_ids:
                                all_reviews_collected.append(review)
                                collected_review_ids.add(review.id)
                                newly_added += 1
                        
                        if len(all_reviews_collected) >= max_reviews_count:
                            break
                
        return all_reviews_collected[:max_reviews_count]

    def parse_reviews(self, article_id: str, max_reviews: int = 500) -> List[Dict[str, Any]]:
        
        if not article_id.isdigit():
            logger.warning(f"ID {article_id} не является числовым артикулом. Парсинг отзывов невозможен.")
            return []
            
        try:
            imt_id = self._fetch_imt_id_for_article(int(article_id))
            if not imt_id:
                logger.warning(f"Не удалось получить imt_id для артикула: {article_id}. Парсинг отзывов невозможен.")
                return []
                
            imt_id_str = str(imt_id)
            
            max_reviews_to_fetch = min(max_reviews, 2000) 

            reviews_pydantic = self.get_all_reviews(
                imt_id=imt_id_str, 
                max_reviews_count=max_reviews_to_fetch,
                timeout=self.DEFAULT_TIMEOUT, 
                retries=self.MAX_RETRIES
            )

            reviews_dict_list = [review.model_dump() for review in reviews_pydantic]
            
            return reviews_dict_list
            
        except ValueError:
            logger.warning(f"Некорректный формат артикула: {article_id}. Должно быть число.")
            return []
        except Exception as e:
            logger.error(f"Ошибка при парсинге отзывов для артикула {article_id}: {e}")
            return []

    def _fetch_imt_id_for_article(self, article_id: int, timeout: int = DEFAULT_TIMEOUT) -> Optional[int]:
        url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()  
            data = response.json()

            if data and "data" in data and "products" in data["data"] and data["data"]["products"]:
                product_data = data["data"]["products"][0]
                imt_id = product_data.get("root") 
                if not imt_id:
                    imt_id = product_data.get("id") 
                
                if imt_id:
                    return int(imt_id)
                else:
                    logger.warning(f"Поля 'root' или 'id' (imt_id) не найдены в данных товара для артикула {article_id}. Данные товара: {str(product_data)[:200]}")
            else:
                logger.warning(f"Неожиданная структура данных или пустой список товаров для артикула {article_id} из {url}. Ответ: {str(data)[:200]}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при получении данных о товаре для артикула {article_id}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON для артикула {article_id}: {e}. Текст ответа: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при получении imt_id для артикула {article_id}: {e}")

        logger.warning(f"Не удалось найти или подтвердить imt_id для артикула {article_id}")
        return None

    def _process_review(self, review: Dict[str, Any], product_info: Dict[str, Any]) -> Dict[str, Any]:
      
        processed = {
            "id": str(review.get("id", "unknown")), 
            "text": review.get("text", ""),
            "rating": review.get("productValuation"),
            "date": review.get("createdDate"),
            "product_id": str(product_info.get("id")) if product_info else str(review.get('nmId', 'unknown')), 
            "product_name": product_info.get("name", "Unknown Product"),
            "author": review.get("userName", "Аноним"),
            "likes": review.get("votes", {}).get("pluses", 0),
            "dislikes": review.get("votes", {}).get("minuses", 0),
            "photos": [],
            "source": "wildberries"
        }

        pros = review.get("pros", "")
        cons = review.get("cons", "")
        if pros:
            processed["text"] += f"\nДостоинства: {pros}"
        if cons:
            processed["text"] += f"\nНедостатки: {cons}"
        processed["text"] = processed["text"].strip()

        photo_base_url = "https://feedbackphotos.wb.ru/"
        photos_data = review.get("photos", [])
        if photos_data and isinstance(photos_data, list):
            for photo_info in photos_data:
                if isinstance(photo_info, dict) and "fullSizeUri" in photo_info:
                    photo_url = photo_base_url + photo_info["fullSizeUri"]
                    processed["photos"].append(photo_url)
                elif isinstance(photo_info, str): 
                    photo_url = photo_base_url + photo_info
                    processed["photos"].append(photo_url)

        return processed
        
    def is_valid_product_id(self, product_id: str) -> bool:
        return product_id is not None and isinstance(product_id, str) and product_id.strip().isdigit()

    def extract_product_id_from_url(self, url: str) -> Optional[str]:

        match = re.search(r'/catalog/(\d+)/detail\.aspx', url)
        if match:
            return match.group(1)
            
        logger.warning(f"Не удалось извлечь ID товара из URL: {url}")
        return None
        
    def get_product_info(self, root_id: int) -> Dict[str, Any]:

        product_info = {"id": str(root_id), "source": "wildberries"}
        
        urls = [
            f"https://card.wb.ru/cards/v1/detail?appType=0&curr=rub&dest=-1257786&spp=30&nm={root_id}",
            f"https://wbx-context-prod.wildberries.ru/api/v1/detail/{root_id}"
        ]

        data = None
        for url in urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)
                if response.status_code == 200:
                    data = response.json()
                    if data and isinstance(data, dict):
                        if "data" in data and "products" in data["data"] and data["data"]["products"]:
                            break 
                        elif "imt_id" in data:
                            data = {"data": {"products": [data]}}
                            break
                        else:
                            data = None
                    else:
                         data = None
            except Exception as e:
                logger.warning(f"Ошибка при запросе информации о товаре с {url}: {e}")
                continue
        
        if not data:
            logger.warning(f"Не удалось получить данные о товаре для Root ID {root_id} ни с одного URL.")
            product_info["name"] = f"Товар Wildberries {root_id}"
            return product_info

        try:
            product_data = data.get("data", {}).get("products", [])[0]
            
            product_info["name"] = product_data.get("name", f"Товар Wildberries {root_id}")
            product_info["brand"] = product_data.get("brand", "Не указан")
            
            price_data = product_data.get("salePriceU") or product_data.get("priceU") or product_data.get("extended", {}).get("basicPriceU")
            if price_data:
                product_info["price"] = price_data / 100.0
            else:
                product_info["price"] = 0.0
            
            product_info["rating"] = product_data.get("reviewRating") or product_data.get("rating", 0.0)
            
            product_info["url"] = f"https://www.wildberries.ru/catalog/{root_id}/detail.aspx"

            imt_id = product_data.get("root") or product_data.get("id")
            if imt_id:
                product_info["image_url"] = None 
            
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Ошибка при парсинге данных о товаре для Root ID {root_id}: {e}")
            if "name" not in product_info:
                product_info["name"] = f"Товар Wildberries {root_id}"
        
        return product_info
        
    @staticmethod
    async def parse_reviews_by_id(
        article_id: str, 
        timeout: int = settings.PARSER_TIMEOUT,
        retries: int = settings.PARSER_RETRIES
    ) -> List[str]:
     
        parser = WildberriesParser()
        parser.DEFAULT_TIMEOUT = timeout
        parser.MAX_RETRIES = retries
        
        reviews_dict_list = parser.parse_reviews(article_id, max_reviews=settings.MAX_REVIEWS)
        
        review_texts = extract_reviews_text(reviews_dict_list)
        
        return review_texts 
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
import time
from collections import Counter
import gc
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.parsers.ozon import OzonParser
from app.services.parsers.wb import WildberriesParser

from app.models.analysis import AnalysisRequest, AnalysisResponse, AnalysisRequestSchema
from app.core.config import settings
from app.services.analyzer import review_analyzer
from app.db.database import get_db
from app.crud.crud_analysis import analysis as crud_analysis
from app.models.analysis import AnalysisStatus

router = APIRouter()

def handle_analysis_error(func):
    import functools
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Ошибка анализа: {str(e)}"
            )
    return wrapper

@router.post("/analyze_reviews", response_model=None)
async def analyze_reviews(request: AnalysisRequestSchema):
    start_time = time.time()
    max_execution_time = 300

    if review_analyzer is None:
        raise HTTPException(status_code=503, detail="Сервис анализа временно недоступен")

    product_info: Dict[str, Any] = {}
    parser: Any = None

    if request.marketplace.lower() == "ozon":
        parser = OzonParser()
    elif request.marketplace.lower() in ["wildberries", "wb"]:
        parser = WildberriesParser()
    else:
        raise HTTPException(status_code=400, detail=f"Неподдерживаемый маркетплейс: {request.marketplace}")

    product_id: str
    if request.url.startswith("http"):
        extracted_id = parser.extract_product_id_from_url(request.url)
        if not extracted_id:
            raise HTTPException(status_code=400, detail=f"Не удалось извлечь ID товара из URL {request.marketplace}")
        product_id = extracted_id
    else:
        product_id = request.url
        if not parser.is_valid_product_id(product_id):
            raise HTTPException(status_code=400, detail=f"Неверный формат ID товара {request.marketplace}")

    raw_reviews_from_parser: List[Dict[str, Any]] = []
    max_reviews_to_parse = min(request.max_reviews, 1000)

    try:
        if request.marketplace.lower() in ["wildberries", "wb"]:
            raw_reviews_from_parser = parser.parse_reviews(product_id, max_reviews=max_reviews_to_parse)
        elif request.marketplace.lower() == "ozon":
            raw_reviews_from_parser = parser.parse_reviews(product_id, max_reviews_to_parse)
        
        if time.time() - start_time > max_execution_time: 
            raise HTTPException(status_code=408, detail="Timeout после парсинга")

        if not raw_reviews_from_parser:
            if hasattr(parser, 'get_product_info'):
                 try:
                    product_info_raw = parser.get_product_info(product_id)
                    if product_info_raw:
                        product_info = {
                            "name": product_info_raw.get("name", f"Товар {request.marketplace} {product_id}"),
                            "id": product_id,
                            "source": request.marketplace,
                            **{k: v for k, v in product_info_raw.items() if k in ["brand", "price", "rating", "image_url", "url"] and v}
                        }
                 except Exception:
                    pass
            if not product_info:
                 product_info = {"name": f"Товар {request.marketplace} {product_id}", "id": product_id, "source": request.marketplace}

            return {
                "product_id": product_id, 
                "product_info": product_info, 
                "reviews_count": 0,
                "sentiment_analysis": {
                    "total": 0, "positive": 0, "negative": 0, "neutral": 0, 
                    "positive_percent": 0, "negative_percent": 0, "neutral_percent": 0, 
                    "aspects": {"positive": {"total_aspect_mentions":0, "categories":[]}, "negative": {"total_aspect_mentions":0, "categories":[]}}
                },
                "topic_analysis": {"topic_summary": {}, "detailed_aspects": []},
                "rating_stats": {"average": 0, "count": 0, "distribution": {str(r): 0 for r in range(1,6)}},
                "marketplace": request.marketplace
            }

    except HTTPException: 
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга отзывов: {str(e)}")

    # Подготавливаем тексты для анализа
    texts_for_analysis = []
    original_ratings = []
    for r_dict in raw_reviews_from_parser:
        text_parts = []
        if r_dict.get("text"): text_parts.append(str(r_dict["text"]))
        if r_dict.get("pros"): text_parts.append("Достоинства: " + str(r_dict["pros"]))
        if r_dict.get("cons"): text_parts.append("Недостатки: " + str(r_dict["cons"]))
        full_text = " ".join(text_parts).strip()
        if len(full_text) > 5:
            texts_for_analysis.append(full_text)
            if r_dict.get("productValuation") is not None:
                 original_ratings.append(int(r_dict["productValuation"]))
            elif r_dict.get("rating") is not None:
                 original_ratings.append(int(r_dict["rating"]))

    max_text_length = 10000
    filtered_texts = []
    for text in texts_for_analysis:
        if len(text) > max_text_length:
            filtered_texts.append(text[:max_text_length])
        else:
            filtered_texts.append(text)
    
    texts_for_analysis = filtered_texts

    if not texts_for_analysis:
        if not product_info and hasattr(parser, 'get_product_info'):
            try: 
                pi_raw = parser.get_product_info(product_id)
                if pi_raw: 
                    product_info = {"name": pi_raw.get("name", f"Товар {request.marketplace} {product_id}"), "id": product_id, "source": request.marketplace, **{k: v for k, v in pi_raw.items() if k in ["brand", "price", "rating", "image_url", "url"] and v}}
            except: 
                pass
        if not product_info: 
            product_name = f"Товар {request.marketplace} {product_id}"
            if hasattr(request, 'url') and request.url:
                if 'ozon.ru/product/' in request.url and '-' in request.url:
                    try:
                        url_parts = request.url.split('/product/')[-1].split('-')
                        if len(url_parts) > 1:
                            potential_name = '-'.join(url_parts[:-1]).replace('-', ' ').strip()
                            if potential_name and len(potential_name) > 5:
                                product_name = potential_name.title()
                    except:
                        pass
                elif 'wildberries.ru' in request.url:
                    try:
                        import urllib.parse
                        parsed_url = urllib.parse.urlparse(request.url)
                        if parsed_url.query:
                            query_params = urllib.parse.parse_qs(parsed_url.query)
                            if 'search' in query_params:
                                potential_name = query_params['search'][0].strip()
                                if potential_name and len(potential_name) > 3:
                                    product_name = potential_name.title()
                    except:
                        pass
            
            product_info = {"name": product_name, "id": product_id, "source": request.marketplace}
        return {
            "product_id": product_id, 
            "product_info": product_info, 
            "reviews_count": 0,
            "sentiment_analysis": {
                "total": 0, "positive": 0, "negative": 0, "neutral": 0, 
                "positive_percent": 0, "negative_percent": 0, "neutral_percent": 0, 
                "aspects": {"positive": {"total_aspect_mentions":0, "categories":[]}, "negative": {"total_aspect_mentions":0, "categories":[]}}
            },
            "topic_analysis": {"topic_summary": {}, "detailed_aspects": []},
            "rating_stats": {"average": 0, "count": 0, "distribution": {str(r): 0 for r in range(1,6)}},
            "marketplace": request.marketplace
        }

    try:
        if time.time() - start_time > max_execution_time:
            raise HTTPException(status_code=408, detail="Timeout перед анализом")

        topic_analysis_result = review_analyzer.analyze_topics(texts_for_analysis)
        detailed_aspects = topic_analysis_result.get("detailed_aspects", [])
        
        sentiment_counts = Counter()
        for result in detailed_aspects:
            sentiment = result.get("sentiment", "neutral")
            sentiment_counts[sentiment] += 1

        rating_distribution = Counter(original_ratings)
        average_rating = sum(original_ratings) / len(original_ratings) if original_ratings else 0

        all_positive_aspects = []
        all_negative_aspects = []
        
        for result in detailed_aspects:
            all_positive_aspects.extend(result.get("positive_aspects", []))
            all_negative_aspects.extend(result.get("negative_aspects", []))
        
        sentiment_analysis_result = review_analyzer.analyze_sentiment(texts_for_analysis)
        
        positive_aspects = sentiment_analysis_result.get("positive_aspects", [])
        negative_aspects = sentiment_analysis_result.get("negative_aspects", [])
        categorized_positive = sentiment_analysis_result.get("categorized_positive", {})
        categorized_negative = sentiment_analysis_result.get("categorized_negative", {})
        
        aspect_categories = defaultdict(lambda: {"positive": 0, "negative": 0})

        for category, aspects in categorized_positive.items():
            category_name = category if category else "ДРУГОЕ"
            aspect_categories[category_name]["positive"] += len(aspects)
            
        for category, aspects in categorized_negative.items():
            category_name = category if category else "ДРУГОЕ"
            aspect_categories[category_name]["negative"] += len(aspects)

        total_reviews = len(texts_for_analysis)
        positive_count = sentiment_counts.get('positive', 0)
        negative_count = sentiment_counts.get('negative', 0)
        neutral_count = sentiment_counts.get('neutral', 0)

        if not product_info and hasattr(parser, 'get_product_info'):
            try:
                product_info_raw = parser.get_product_info(product_id)
                if product_info_raw:
                    product_info = {
                        "name": product_info_raw.get("name", f"Товар {request.marketplace} {product_id}"),
                        "id": product_id,
                        "source": request.marketplace,
                        **{k: v for k, v in product_info_raw.items() if k in ["brand", "price", "rating", "image_url", "url"] and v}
                    }
            except:
                pass

        if not product_info:
            product_info = {"name": f"Товар {request.marketplace} {product_id}", "id": product_id, "source": request.marketplace}

        response_data = {
            "product_id": product_id,
            "product_info": product_info,
            "reviews_count": total_reviews,
            "sentiment_analysis": {
                "total": total_reviews,
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "positive_percent": round((positive_count / total_reviews) * 100, 1) if total_reviews > 0 else 0,
                "negative_percent": round((negative_count / total_reviews) * 100, 1) if total_reviews > 0 else 0,
                "neutral_percent": round((neutral_count / total_reviews) * 100, 1) if total_reviews > 0 else 0,
                "aspects": {
                    "positive": {"total_aspect_mentions": len(positive_aspects), "categories": [{"text": aspect[0], "count": aspect[1]} for aspect in positive_aspects[:20]]},
                    "negative": {"total_aspect_mentions": len(negative_aspects), "categories": [{"text": aspect[0], "count": aspect[1]} for aspect in negative_aspects[:20]]}
                }
            },
            "aspect_statistics": {
                "total": total_reviews,
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "aspect_summary": {
                    "aspect_categories": dict(aspect_categories),
                    "positive_aspects": [{"text": aspect[0], "count": aspect[1]} for aspect in positive_aspects[:20]],
                    "negative_aspects": [{"text": aspect[0], "count": aspect[1]} for aspect in negative_aspects[:20]]
                }
            },
            "topic_analysis": [],
            "rating_stats": {
                "average": round(average_rating, 1),
                "count": len(original_ratings),
                "distribution": {str(i): rating_distribution.get(i, 0) for i in range(1, 6)}
            },
            "marketplace": request.marketplace
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")
    finally:
        gc.collect()

@router.post("/analyze_review_text", response_model=Dict[str, Any])
async def analyze_review_text(text: str = Body(..., embed=True, description="Текст отзыва для анализа")):
    if review_analyzer is None:
        raise HTTPException(status_code=503, detail="Сервис анализа временно недоступен (RA). Повторите запрос позже.")

    try:
        aspect_sentiment_result = review_analyzer.analyze_review(text)
        topics_result = review_analyzer.analyze_topics([text])

        return {
            "text": text,
            "sentiment_analysis": aspect_sentiment_result,
            "topic_analysis": topics_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе текста: {str(e)}")

@router.post("/analyze_topics", response_model=Dict[str, Any])
@handle_analysis_error
async def analyze_topics(texts: List[str] = Body(...)):
    if not texts:
        return {"topic_summary": {}, "detailed_aspects": []}

    result = review_analyzer.analyze_topics(texts)
    gc.collect()
    
    return result

@router.post("/analyze_sentiment", response_model=Dict[str, Any])
@handle_analysis_error
async def analyze_sentiment(texts: List[str] = Body(...)):
    if not texts:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "positive_percent": 0,
            "negative_percent": 0,
            "neutral_percent": 0,
            "aspects": {
                "aspect_categories": {},
                "positive_aspects": [],
                "negative_aspects": []
            }
        }

    result = review_analyzer.analyze_sentiment(texts)
    gc.collect()
    
    return result

@router.post("/analyze_sentiment_single", response_model=Dict[str, Any]) 
@handle_analysis_error
async def analyze_sentiment_single(text: str = Body(..., embed=True)):
    if not review_analyzer:
        raise HTTPException(status_code=503, detail="Сервис анализа недоступен.")
    
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Текст для анализа не может быть пустым.")

    try:
        result = review_analyzer.analyze_sentiment_single(text)
        
        response_data = {
            "text": text,
            "sentiment": result.get("sentiment", "neutral"),
            "positive_aspects": result.get("positive_aspects", []),
            "negative_aspects": result.get("negative_aspects", []),
            "categorized_positive": result.get("categorized_positive", {}),
            "categorized_negative": result.get("categorized_negative", {})
        }
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера при анализе текста: {str(e)}") 

@router.post("/save_analysis", response_model=Dict[str, Any])
async def save_analysis_results(
    request_id: int = Body(..., description="ID запроса анализа"),
    positive_aspects: List[Dict[str, Any]] = Body(..., description="Список положительных аспектов"),
    negative_aspects: List[Dict[str, Any]] = Body(..., description="Список отрицательных аспектов"),
    aspect_categories: Dict[str, Any] = Body(..., description="Категории аспектов"),
    reviews_count: int = Body(..., description="Количество проанализированных отзывов"),
    sentiment_summary: Dict[str, Any] = Body(..., description="Сводка по тональности"),
    product_info: Optional[Dict[str, Any]] = Body(None, description="Информация о товаре"),
    db: AsyncSession = Depends(get_db)
):
    
    try:
        request = await crud_analysis.get(db, id=request_id)
        if not request:
            raise HTTPException(status_code=404, detail=f"Запрос с ID={request_id} не найден")
        
        await crud_analysis.update_status(db, db_obj=request, status=AnalysisStatus.COMPLETED)
        
        try:
            result = await crud_analysis.save_result(
                db,
                request_id=request_id,
                positive_aspects=positive_aspects,
                negative_aspects=negative_aspects,
                aspect_categories=aspect_categories,
                reviews_count=reviews_count,
                sentiment_summary=sentiment_summary,
                product_info=product_info
            )
            return {"success": True, "result_id": result.id}
        except Exception as e:
            await crud_analysis.update_status(
                db, 
                db_obj=request, 
                status=AnalysisStatus.FAILED, 
                error_message=f"Ошибка сохранения результатов: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=f"Ошибка сохранения результатов: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Непредвиденная ошибка: {str(e)}") 

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": str(time.time())} 
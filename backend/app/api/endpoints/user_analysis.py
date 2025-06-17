from fastapi import APIRouter, HTTPException, Depends, Query, Body, Path, Request, BackgroundTasks
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import re
import datetime
import asyncio

from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.crud.crud_analysis import analysis as crud_analysis
from app.schemas.analysis import (
    AnalysisRequestCreate, 
    AnalysisRequestResponse, 
    AnalysisResultResponse,
    AnalysisRequestWithResults
)
from app.models.analysis import AnalysisStatus
from app.services.parsers.wb import WildberriesParser
from app.services.parsers.ozon import OzonParser
from app.services.analyzer import review_analyzer

router = APIRouter()

cancelled_analyses = set()

async def process_analysis_background(analysis_id: int):

    from app.db.database import get_async_session
    
    async for db in get_async_session():
        try:
            analysis = await crud_analysis.get(db, id=analysis_id)
            if not analysis:
                return
            
            existing_result = await crud_analysis.get_result(db, request_id=analysis_id)
            if existing_result:
                await crud_analysis.update_status(db, db_obj=analysis, status=AnalysisStatus.COMPLETED)
                await crud_analysis.update_progress(
                    db, 
                    db_obj=analysis, 
                    progress_percentage=100.0,
                    current_stage="completed",
                    processed_reviews=existing_result.reviews_count,
                    total_reviews=existing_result.reviews_count
                )
                await db.commit()
                return
            
            await crud_analysis.update_status(db, db_obj=analysis, status=AnalysisStatus.PROCESSING)
            await crud_analysis.update_progress(
                db, 
                db_obj=analysis, 
                progress_percentage=5.0,
                current_stage="parsing",
                processed_reviews=0,
                total_reviews=analysis.max_reviews
            )
            await db.commit()
            
            if analysis.marketplace == "wb":
                parser = WildberriesParser()
            elif analysis.marketplace == "ozon":
                parser = OzonParser()
            else:
                raise ValueError(f"Неподдерживаемый маркетплейс: {analysis.marketplace}")
            
            await crud_analysis.update_progress(
                db, 
                db_obj=analysis, 
                progress_percentage=10.0,
                current_stage="parsing",
                processed_reviews=0,
                total_reviews=analysis.max_reviews
            )
            await db.commit()
            
            reviews = parser.parse_reviews(analysis.product_id, max_reviews=analysis.max_reviews)
            product_info = parser.get_product_info(int(analysis.product_id))
            
            await crud_analysis.update_progress(
                db, 
                db_obj=analysis, 
                progress_percentage=30.0,
                current_stage="sentiment_analysis",
                processed_reviews=0,
                total_reviews=len(reviews)
            )
            await db.commit()
            
            if not reviews:
                await crud_analysis.update_status(
                    db, 
                    db_obj=analysis, 
                    status=AnalysisStatus.FAILED, 
                    error_message="Не удалось получить отзывы"
                )
                await db.commit()
                return
            
            
            review_texts = [review.get("text", "") for review in reviews if review.get("text")]
            
            analyzed_reviews = []
            total_texts = len(review_texts)
            
            for i, text in enumerate(review_texts):
                if analysis_id in cancelled_analyses:
                    await crud_analysis.update_status(
                        db, 
                        db_obj=analysis, 
                        status=AnalysisStatus.CANCELLED, 
                        error_message="Анализ отменен пользователем"
                    )
                    await db.commit()
                    cancelled_analyses.discard(analysis_id)  
                    return
                
                try:
                    result = review_analyzer.analyze_review(text)
                    analyzed_reviews.append(result)
                    
                    if (i + 1) % 3 == 0 or (i + 1) == total_texts:
                        progress = min(80, 30 + int((i + 1) / total_texts * 50))  # 30-80%
                        stage = "sentiment_analysis" if progress < 70 else "aspect_analysis"
                        stage_name = "Анализ тональности" if progress < 70 else "Анализ аспектов"
                        
                        await crud_analysis.update_progress(
                            db, 
                            db_obj=analysis, 
                            progress_percentage=float(progress),
                            current_stage=stage,
                            processed_reviews=i + 1,
                            total_reviews=total_texts
                        )
                        await db.commit()
                        
                except Exception as e:
                    continue
            
            await crud_analysis.update_progress(
                db, 
                db_obj=analysis, 
                progress_percentage=85.0,
                current_stage="finalizing",
                processed_reviews=total_texts,
                total_reviews=total_texts
            )
            await db.commit()
            
            stats = review_analyzer.get_summary_statistics(analyzed_reviews)
            
            sentiment_results = review_analyzer.analyze_sentiment(review_texts[:500])
            
            await crud_analysis.update_progress(
                db, 
                db_obj=analysis, 
                progress_percentage=95.0,
                current_stage="finalizing",
                processed_reviews=total_texts,
                total_reviews=total_texts
            )
            await db.commit()
            
            categorized_positive = sentiment_results.get("categorized_positive", {})
            categorized_negative = sentiment_results.get("categorized_negative", {})
            
            flat_positive_aspects = []
            flat_negative_aspects = []
            
            for aspect_tuple in sentiment_results.get("positive_aspects", []):
                if isinstance(aspect_tuple, tuple) and len(aspect_tuple) >= 2:
                    flat_positive_aspects.append({"text": aspect_tuple[0], "count": aspect_tuple[1]})
                elif isinstance(aspect_tuple, dict):
                    flat_positive_aspects.append({"text": aspect_tuple.get("text", ""), "count": aspect_tuple.get("count", 1)})
            
            for aspect_tuple in sentiment_results.get("negative_aspects", []):
                if isinstance(aspect_tuple, tuple) and len(aspect_tuple) >= 2:
                    flat_negative_aspects.append({"text": aspect_tuple[0], "count": aspect_tuple[1]})
                elif isinstance(aspect_tuple, dict):
                    flat_negative_aspects.append({"text": aspect_tuple.get("text", ""), "count": aspect_tuple.get("count", 1)})
            
            def build_categories_structure(categorized_aspects):
                categories = []
                total_mentions = 0
                
                for category_name, aspects_list in categorized_aspects.items():
                    if not aspects_list:
                        continue
                    
                    category_aspects = []
                    category_mentions = 0
                    
                    for aspect_item in aspects_list:
                        if isinstance(aspect_item, tuple) and len(aspect_item) >= 2:
                            text, count = aspect_item[0], aspect_item[1]
                        elif isinstance(aspect_item, dict):
                            text, count = aspect_item.get("text", ""), aspect_item.get("count", 1)
                        else:
                            continue
                        
                        category_aspects.append({"text": text, "count": count})
                        category_mentions += count
                    
                    if category_aspects:
                        categories.append({
                            "name": category_name,
                            "aspects": category_aspects,
                            "total_mentions_in_category": category_mentions
                        })
                        total_mentions += category_mentions
                
                return {"categories": categories, "total_aspect_mentions": total_mentions}
            
            structured_aspect_categories = {
                "positive": build_categories_structure(categorized_positive),
                "negative": build_categories_structure(categorized_negative)
            }
            
            total_reviews = len(reviews)
            positive_count = len([r for r in analyzed_reviews if r.get("sentiment") == "positive"])
            negative_count = len([r for r in analyzed_reviews if r.get("sentiment") == "negative"])
            neutral_count = total_reviews - positive_count - negative_count
            
            results_data = {
                "positive_aspects": flat_positive_aspects,
                "negative_aspects": flat_negative_aspects,
                "aspect_categories": structured_aspect_categories,
                "reviews_count": total_reviews,
                "sentiment_summary": {
                    "total": total_reviews,
                    "positive": positive_count,
                    "negative": negative_count,
                    "neutral": neutral_count,
                    "positive_percent": round((positive_count / max(1, total_reviews)) * 100, 1),
                    "negative_percent": round((negative_count / max(1, total_reviews)) * 100, 1),
                    "neutral_percent": round((neutral_count / max(1, total_reviews)) * 100, 1),
                },
                "product_info": product_info
            }
            
            await crud_analysis.save_result(
                db,
                request_id=analysis_id,
                positive_aspects=results_data["positive_aspects"],
                negative_aspects=results_data["negative_aspects"],
                aspect_categories=results_data["aspect_categories"],
                reviews_count=results_data["reviews_count"],
                sentiment_summary=results_data["sentiment_summary"],
                product_info=results_data["product_info"]
            )
            
            await crud_analysis.update_status(db, db_obj=analysis, status=AnalysisStatus.COMPLETED)
            await crud_analysis.update_progress(
                db, 
                db_obj=analysis, 
                progress_percentage=100.0,
                current_stage="completed",
                processed_reviews=total_texts,
                total_reviews=total_texts
            )
            await db.commit()
            
        except Exception as e:
            try:
                analysis = await crud_analysis.get(db, id=analysis_id)
                if analysis:
                    await crud_analysis.update_status(
                        db, 
                        db_obj=analysis, 
                        status=AnalysisStatus.FAILED, 
                        error_message=str(e)
                    )
                    await db.commit()
            except Exception as update_error:
                pass
        finally:
            await db.close()
        break  

@router.get("/", response_model=List[AnalysisRequestResponse])
async def get_user_analyses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    request: Request = None
):
    
    try:
        analyses = await crud_analysis.get_multi_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
        
        response_analyses = []
        for analysis in analyses:
            analysis_dict = {
                "id": analysis.id,
                "user_id": analysis.user_id,
                "product_id": analysis.product_id,
                "marketplace": analysis.marketplace,
                "status": analysis.status,
                "error_message": analysis.error_message,
                "created_at": analysis.created_at,
                "updated_at": analysis.updated_at,
                "url": analysis.url,
                "max_reviews": analysis.max_reviews,
                "results": None
            }
            
            if analysis.results:
                analysis_dict["product_name"] = (
                    analysis.results.product_info.get("name") 
                    if analysis.results.product_info and isinstance(analysis.results.product_info, dict)
                    else None
                )
                analysis_dict["reviews_count"] = analysis.results.reviews_count
            else:
                analysis_dict["product_name"] = None
                analysis_dict["reviews_count"] = 0
            
            response_analyses.append(AnalysisRequestResponse(**analysis_dict))
        
        return response_analyses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

def extract_product_id(url: str, marketplace: str) -> str:

    if marketplace == "wb":
        match = re.search(r'/catalog/(\d+)/', url)
        if match:
            return match.group(1)
    elif marketplace == "ozon":
        match = re.search(r'product/(\d+)/', url)
        if match:
            return match.group(1)
    
    return url.split('/')[-1].split('.')[0]

@router.post("/", response_model=AnalysisRequestResponse)
async def create_analysis(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    analysis_in: AnalysisRequestCreate,
    background_tasks: BackgroundTasks
):

    try:
        if not analysis_in.product_id:
            product_id = extract_product_id(analysis_in.url, analysis_in.marketplace)
            analysis_in_dict = analysis_in.model_dump()
            analysis_in_dict["product_id"] = product_id
            analysis_obj = AnalysisRequestCreate(**analysis_in_dict)
        else:
            analysis_obj = analysis_in
            
        analysis = await crud_analysis.create_with_user(db, obj_in=analysis_obj, user_id=current_user.id)
        
        background_tasks.add_task(process_analysis_background, analysis.id)
        
        return AnalysisRequestResponse(
            id=analysis.id,
            user_id=analysis.user_id,
            product_id=analysis.product_id,
            marketplace=analysis.marketplace,
            status=analysis.status,
            error_message=analysis.error_message,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            url=analysis.url,
            max_reviews=analysis.max_reviews,
            results=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось создать анализ: {str(e)}")

@router.get("/{analysis_id}", response_model=AnalysisRequestWithResults)
async def get_analysis(
    analysis_id: int = Path(..., description="ID анализа"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    analysis = await crud_analysis.get_with_result(db, id=analysis_id, user_id=current_user.id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")
    return analysis

@router.delete("/{analysis_id}", response_model=dict)
async def delete_analysis(
    analysis_id: int = Path(..., description="ID анализа"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    analysis = await crud_analysis.get(db, id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")
    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому анализу")
    
    await crud_analysis.remove(db, id=analysis_id)
    return {"status": "success", "message": "Анализ успешно удален"}

@router.get("/progress/{analysis_id}")
async def get_analysis_progress(
    analysis_id: int = Path(..., description="ID анализа"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    analysis = await crud_analysis.get(db, id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")
    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому анализу")
    
    try:
        progress_percentage = analysis.progress_percentage or 0.0
        current_stage = analysis.current_stage or "pending"
        processed_reviews = analysis.processed_reviews or 0
        total_reviews = analysis.total_reviews or analysis.max_reviews or 100
        
        stage_names = {
            "pending": "Ожидание",
            "parsing": "Загрузка отзывов", 
            "sentiment_analysis": "Анализ тональности",
            "aspect_analysis": "Анализ аспектов",
            "finalizing": "Формирование отчета",
            "completed": "Завершено",
            "failed": "Ошибка"
        }
        stage_name = stage_names.get(current_stage, "Обработка")
        
        estimated_time_remaining = None
        if analysis.status == "processing" and progress_percentage > 0 and progress_percentage < 100:
            now = datetime.datetime.now()
            created_time = analysis.created_at
            if created_time.tzinfo is not None:
                created_time = created_time.replace(tzinfo=None)
            elapsed = (now - created_time).total_seconds()
            
            if progress_percentage > 5:  
                total_estimated_time = (elapsed / progress_percentage) * 100
                estimated_time_remaining = max(0, int(total_estimated_time - elapsed))
        
        progress_data = {
            "analysis_id": analysis.id,
            "status": analysis.status,
            "progress_percentage": round(progress_percentage, 1),
            "stage": current_stage,
            "stage_name": stage_name,
            "processed_reviews": processed_reviews,
            "total_reviews": total_reviews,
            "estimated_time_remaining": estimated_time_remaining,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at
        }
        
    except Exception as e:
        progress_data = {
            "analysis_id": analysis.id,
            "status": analysis.status,
            "progress_percentage": 0.0,
            "stage": "pending",
            "stage_name": "Ожидание",
            "processed_reviews": 0,
            "total_reviews": analysis.max_reviews or 100,
            "estimated_time_remaining": None,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at
        }
    
    return progress_data

@router.post("/{analysis_id}/cancel", response_model=dict)
async def cancel_analysis(
    analysis_id: int = Path(..., description="ID анализа"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    analysis = await crud_analysis.get(db, id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")
    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому анализу")
    
    if analysis.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Нельзя отменить анализ со статусом '{analysis.status}'"
        )
    
    cancelled_analyses.add(analysis_id)
    
    await crud_analysis.update_status(
        db, 
        db_obj=analysis, 
        status=AnalysisStatus.CANCELLED, 
        error_message="Анализ отменен пользователем"
    )
    await db.commit()
    
    return {"status": "success", "message": "Анализ успешно отменен"}

 
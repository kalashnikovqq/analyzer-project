from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any

from app.services.parsers.ozon import OzonParser
from app.services.parsers.wb import WildberriesParser
from app.models.review import ReviewModel

router = APIRouter()

@router.get("/parse_reviews", response_model=List[Dict[str, Any]])
async def parse_reviews(
    url: str = Query(..., description="URL товара или ID товара"),
    marketplace: str = Query(..., description="Маркетплейс (ozon, wildberries)"),
    max_reviews: int = Query(30, description="Количество отзывов для парсинга")
):
    
    if marketplace.lower() == "ozon":
        parser = OzonParser()
        
        if url.startswith("http"):
            product_id = parser.extract_product_id_from_url(url)
            if not product_id:
                raise HTTPException(status_code=400, detail="Не удалось извлечь ID товара из URL Ozon")
        else:
            product_id = url
            if not parser.is_valid_product_id(product_id):
                raise HTTPException(status_code=400, detail="Неверный формат ID товара Ozon")
                
        reviews = parser.parse_reviews(product_id, max_reviews)
        return reviews
        
    elif marketplace.lower() == "wildberries" or marketplace.lower() == "wb":
        parser = WildberriesParser()
        
        if url.startswith("http"):
            product_id = parser.extract_product_id_from_url(url)
            if not product_id:
                raise HTTPException(status_code=400, detail="Не удалось извлечь ID товара из URL Wildberries")
        else:
            product_id = url
            if not parser.is_valid_product_id(product_id):
                raise HTTPException(status_code=400, detail="Неверный формат ID товара Wildberries")
                
        reviews = parser.parse_reviews(product_id, max_reviews)
        return reviews
        
    else:
        raise HTTPException(status_code=400, detail=f"Неподдерживаемый маркетплейс: {marketplace}. Поддерживаются: ozon, wildberries")

@router.get("/extract_product_id", response_model=Dict[str, str])
async def extract_product_id(
    url: str = Query(..., description="URL товара"),
    marketplace: str = Query(..., description="Маркетплейс (ozon, wildberries)")
):

    if marketplace.lower() == "ozon":
        parser = OzonParser()
        product_id = parser.extract_product_id_from_url(url)
        if not product_id:
            raise HTTPException(status_code=400, detail="Не удалось извлечь ID товара из URL Ozon")
        return {"product_id": product_id}
        
    elif marketplace.lower() == "wildberries" or marketplace.lower() == "wb":
        parser = WildberriesParser()
        product_id = parser.extract_product_id_from_url(url)
        if not product_id:
            raise HTTPException(status_code=400, detail="Не удалось извлечь ID товара из URL Wildberries")
        return {"product_id": product_id}
        
    else:
        raise HTTPException(status_code=400, detail=f"Неподдерживаемый маркетплейс: {marketplace}. Поддерживаются: Ozon, Wildberries")

@router.get("/validate_product_id", response_model=Dict[str, bool])
async def validate_product_id(
    product_id: str = Query(..., description="ID товара для проверки"),
    marketplace: str = Query(..., description="Маркетплейс (ozon, wildberries)")
):

    if marketplace.lower() == "ozon":
        parser = OzonParser()
        is_valid = parser.is_valid_product_id(product_id)
        return {"is_valid": is_valid}
        
    elif marketplace.lower() == "wildberries" or marketplace.lower() == "wb":
        parser = WildberriesParser()
        is_valid = parser.is_valid_product_id(product_id)
        return {"is_valid": is_valid}
        
    else:
        raise HTTPException(status_code=400, detail=f"Неподдерживаемый маркетплейс: {marketplace}. Поддерживаются: ozon, wildberries") 
from typing import AsyncGenerator
import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.db.database import Base
from app.db.database import engine

from app.models.user import User
from app.models.analysis import AnalysisRequest, AnalysisResult

logger = logging.getLogger(__name__)

async def init_db() -> None:

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_db()) 
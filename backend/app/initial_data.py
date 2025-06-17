import logging
import asyncio
from app.db.session import async_session
from app.crud.crud_user import CRUDUser
from app.models.user import User

crud_user = CRUDUser(User)
from app.schemas.user import UserCreate
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_initial_users():
    try:
        async with async_session() as session:
            async with session.begin():
                admin_user = UserCreate(
                    email="administrator@feedbacklab.ru",
                    password="FeedbackLab2024!",
                    is_superuser=True,
                    full_name="Администратор системы"
                )
                await crud_user.create(session, obj_in=admin_user)
                
                analyst_user = UserCreate(
                    email="analyst@feedbacklab.ru",
                    password="Analyst2024!",
                    is_superuser=False,
                    full_name="Аналитик"
                )
                await crud_user.create(session, obj_in=analyst_user)
    except Exception as e:
        logger.error(f"Ошибка при создании начальных пользователей: {e}")

async def init():
    await create_initial_users()
    logger.info("Начальные данные созданы")

if __name__ == "__main__":
    asyncio.run(init()) 
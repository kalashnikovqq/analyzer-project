from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

Base = declarative_base()

engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=True,
    future=True,
    poolclass=NullPool,
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db() -> AsyncSession:

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 

async def get_async_session():

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 
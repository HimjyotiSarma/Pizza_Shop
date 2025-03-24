from sqlmodel import create_engine, SQLModel, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

from src.config import settings

# Create new Engine
engine = AsyncEngine(
    create_engine(
        url=settings.DATABASE_URL,
        echo=True
    )
)

# Intialize the engine

async def init_db():
    async with engine.begin() as conn:
        try:
            await conn.run_sync(SQLModel.metadata.create_all)
        except Exception as e:
            logging.error(f"Database Initialization Failed: {e}")
            raise e


# Define New Session Maker

async def get_session():
    Session= sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=True
    )

    async with Session() as session:
        yield session
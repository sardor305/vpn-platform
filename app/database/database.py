from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config.config import config

engine = create_async_engine(
    config.DATABASE_URL,
    echo=True
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False
)

async def check_db_connection():
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL bilan ulanish muvaffaqiyatli!")
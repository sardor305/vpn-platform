from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config.config import config


engine = create_async_engine(
    config.DATABASE_URL,
    echo=True,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def check_db_connection():
    async with engine.begin() as conn:

        result = await conn.execute(
            text("SELECT current_database(), current_user")
        )
        print("Database:", result.fetchall())

        result = await conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'vpn_accounts'
                ORDER BY ordinal_position
            """)
        )
        print("Columns:", result.fetchall())

        print("✅ PostgreSQL bilan ulanish muvaffaqiyatli!")


async def get_session():
    async with async_session() as session:
        yield session
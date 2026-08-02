from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:

        stmt = select(User).where(
            User.id == user_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_telegram_id(
        self,
        telegram_id: int
    ) -> User | None:

        stmt = select(User).where(
            User.telegram_id == telegram_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        language_code: str,
    ) -> User:

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )

        self.session.add(user)

        await self.session.flush()

        await self.session.refresh(user)

        return user
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.user_repository = UserRepository(session)

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:

        return await self.user_repository.get_by_id(
            user_id
        )

    async def get_by_telegram_id(
        self,
        telegram_id: int,
    ) -> User | None:

        return await self.user_repository.get_by_telegram_id(
            telegram_id
        )

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        language_code: str,
    ) -> tuple[User, bool]:

        user = await self.user_repository.get_by_telegram_id(
            telegram_id
        )

        created = False

        if user is None:
            user = await self.user_repository.create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
            )

            created = True

        return user, created

    async def get_all_users(
        self,
    ) -> list[User]:

        return await self.user_repository.get_all()

    async def count_users(
        self,
    ) -> int:

        return await self.user_repository.count()
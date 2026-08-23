from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting


class SettingRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_key(
        self,
        key: str,
    ) -> Setting | None:

        stmt = select(Setting).where(
            Setting.key == key
        )

        result = await self.session.execute(
            stmt
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        key: str,
        value: str,
    ) -> Setting:

        setting = Setting(
            key=key,
            value=value,
        )

        self.session.add(setting)

        await self.session.flush()

        await self.session.refresh(setting)

        return setting

    async def update(
        self,
        setting: Setting,
        value: str,
    ) -> Setting:

        setting.value = value

        await self.session.flush()

        await self.session.refresh(setting)

        return setting
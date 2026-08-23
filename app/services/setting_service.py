from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from app.repositories.setting_repository import SettingRepository


class SettingService:

    DAILY_PRICE_KEY = "daily_price"

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.setting_repository = SettingRepository(
            session
        )

    async def get_daily_price(
        self,
    ) -> int:

        setting = await self.setting_repository.get_by_key(
            self.DAILY_PRICE_KEY
        )

        if setting is None:
            setting = await self.setting_repository.create(
                key=self.DAILY_PRICE_KEY,
                value="1000",
            )

        try:
            return int(setting.value)

        except (TypeError, ValueError):
            raise ValueError(
                "1 kunlik narx noto‘g‘ri sozlangan."
            )

    async def set_daily_price(
        self,
        price: int,
    ) -> Setting:

        if price <= 0:
            raise ValueError(
                "1 kunlik narx 0 dan katta bo‘lishi kerak."
            )

        setting = await self.setting_repository.get_by_key(
            self.DAILY_PRICE_KEY
        )

        if setting is None:

            return await self.setting_repository.create(
                key=self.DAILY_PRICE_KEY,
                value=str(price),
            )

        return await self.setting_repository.update(
            setting=setting,
            value=str(price),
        )

    async def calculate_price(
        self,
        duration_days: int,
    ) -> int:

        if duration_days <= 0:
            raise ValueError(
                "Muddat 0 dan katta bo‘lishi kerak."
            )

        daily_price = await self.get_daily_price()

        return daily_price * duration_days
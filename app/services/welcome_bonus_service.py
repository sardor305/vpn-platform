from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_bonus import UserBonus
from app.repositories.bonus_traffic_repository import (
    BonusTrafficRepository,
)
from app.repositories.user_bonus_repository import UserBonusRepository
from app.services.service_access_service import ServiceAccessService


@dataclass
class WelcomeBonusResult:
    success: bool
    message: str
    bonus: UserBonus | None = None


class WelcomeBonusService:
    WELCOME_BONUS_TYPE = "welcome"
    WELCOME_DURATION_DAYS = 3
    WELCOME_TRAFFIC_BYTES = (
        3 * 1024 * 1024 * 1024
    )

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.user_bonus_repository = UserBonusRepository(
            session
        )

        self.bonus_traffic_repository = BonusTrafficRepository(
            session
        )

        self.service_access_service = ServiceAccessService(
            session
        )

    async def get_existing_welcome(
        self,
        user_id: int,
    ) -> UserBonus | None:
        return await self.user_bonus_repository.get_welcome_by_user(
            user_id
        )

    async def can_claim(
        self,
        user_id: int,
    ) -> bool:
        existing = await self.get_existing_welcome(user_id)

        return existing is None

    async def claim(
        self,
        user_id: int,
    ) -> WelcomeBonusResult:
        # Serialize Welcome Bonus claims for the same user.
        # The transaction-scoped PostgreSQL advisory lock is held
        # until the current transaction ends, so parallel claims
        # cannot both pass the "no existing Welcome Bonus" check.
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(:user_id)"),
            {"user_id": user_id},
        )

        existing = await self.get_existing_welcome(
            user_id
        )

        if existing is not None:
            return WelcomeBonusResult(
                success=False,
                message="Welcome Bonus sizga avval berilgan.",
                bonus=existing,
            )

        bonus = await self.user_bonus_repository.create(
            user_id=user_id,
            bonus_type=self.WELCOME_BONUS_TYPE,
            duration_days=self.WELCOME_DURATION_DAYS,
            status="pending",
            start_date=None,
            end_date=None,
            activated_at=None,
        )

        traffic = await self.bonus_traffic_repository.create(
            bonus_id=bonus.id,
            traffic_limit_bytes=self.WELCOME_TRAFFIC_BYTES,
            traffic_used_bytes=0,
        )

        bonus.traffic = traffic

        await self.service_access_service.sync_user(
            user_id=user_id
        )

        return WelcomeBonusResult(
            success=True,
            message=(
                "Welcome Bonus muvaffaqiyatli olindi: "
                "3 kun + 3 GB."
            ),
            bonus=bonus,
        )
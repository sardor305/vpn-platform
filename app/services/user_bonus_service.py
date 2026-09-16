from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_bonus import UserBonus
from app.repositories.user_bonus_repository import UserBonusRepository
from app.utils.datetime import utc_now


class UserBonusService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.user_bonus_repository = UserBonusRepository(
            session
        )

    async def get_bonus(
        self,
        bonus_id: int,
    ) -> UserBonus | None:

        return await (
            self.user_bonus_repository
            .get_by_id(bonus_id)
        )

    async def get_active_bonus(
        self,
        user_id: int,
    ) -> UserBonus | None:

        return await (
            self.user_bonus_repository
            .get_active_by_user(user_id)
        )

    async def get_pending_bonuses(
        self,
        user_id: int,
    ) -> list[UserBonus]:

        return await (
            self.user_bonus_repository
            .get_pending_by_user(user_id)
        )

    async def get_bonus_history(
        self,
        user_id: int,
    ) -> list[UserBonus]:

        return await (
            self.user_bonus_repository
            .get_all_by_user(user_id)
        )

    async def get_bonus_history_paginated(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[UserBonus], int]:

        return await (
            self.user_bonus_repository
            .get_all_by_user_paginated(
                user_id=user_id,
                page=page,
                page_size=page_size,
            )
        )

    async def get_all_active_bonuses(
        self,
    ) -> list[UserBonus]:

        return await (
            self.user_bonus_repository
            .get_all_active()
        )

    async def get_all_active_for_expiry_check(
        self,
    ) -> list[UserBonus]:

        return await (
            self.user_bonus_repository
            .get_all_active_for_expiry_check()
        )

    async def get_all_pending_bonuses(
        self,
    ) -> list[UserBonus]:

        return await (
            self.user_bonus_repository
            .get_all_pending()
        )

    async def create_bonus(
        self,
        user_id: int,
        bonus_type: str,
        duration_days: int,
        bonus_number: int | None = None,
        reason: str | None = None,
        referral_id: int | None = None,
    ) -> UserBonus:

        if duration_days <= 0:
            raise ValueError(
                "Bonus duration must be greater than zero."
            )

        if not bonus_type:
            raise ValueError(
                "Bonus type is required."
            )

        normalized_reason = reason.strip() if reason else None
        if bonus_type.strip().lower() == "admin" and not normalized_reason:
            raise ValueError(
                "Admin Bonus reason is required."
            )

        return await (
            self.user_bonus_repository
            .create(
                user_id=user_id,
                bonus_type=bonus_type,
                duration_days=duration_days,
                reason=normalized_reason,
                status="pending",
                bonus_number=bonus_number,
                referral_id=referral_id,
                start_date=None,
                end_date=None,
                activated_at=None,
            )
        )

    async def activate_bonus(
        self,
        bonus: UserBonus,
        start_date: datetime,
    ) -> UserBonus:

        if bonus.status != "pending":
            raise ValueError(
                "Only pending bonuses can be activated."
            )

        if start_date.tzinfo is None:
            start_date = start_date.replace(
                tzinfo=utc_now().tzinfo
            )

        end_date = (
            start_date
            + timedelta(days=bonus.duration_days)
        )

        bonus.start_date = start_date
        bonus.end_date = end_date
        bonus.activated_at = utc_now()
        bonus.status = "active"

        return await (
            self.user_bonus_repository
            .update(bonus)
        )

    async def expire_bonus(
        self,
        bonus: UserBonus,
        now: datetime | None = None,
    ) -> UserBonus:

        if bonus.status != "active":
            raise ValueError(
                "Only active bonuses can be expired."
            )

        current_time = now or utc_now()

        if bonus.end_date is None:
            raise ValueError(
                "Active bonus must have an end date."
            )

        if bonus.end_date > current_time:
            raise ValueError(
                "Bonus has not expired yet."
            )

        bonus.status = "expired"

        return await (
            self.user_bonus_repository
            .update(bonus)
        )

    async def revoke_bonus(
        self,
        bonus: UserBonus,
    ) -> UserBonus:

        if bonus.status == "expired":
            raise ValueError(
                "Expired bonus cannot be revoked."
            )

        if bonus.status == "revoked":
            raise ValueError(
                "Bonus is already revoked."
            )

        bonus.status = "revoked"

        return await (
            self.user_bonus_repository
            .update(bonus)
        )
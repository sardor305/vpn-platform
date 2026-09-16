from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.referral import Referral


class ReferralRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self,
        referral_id: int,
    ) -> Referral | None:
        result = await self.session.execute(
            select(Referral).where(
                Referral.id == referral_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_invited_user(
        self,
        referral_id: int,
    ) -> Referral | None:
        """Return a Referral together with the invited user's Telegram ID."""

        result = await self.session.execute(
            select(Referral)
            .options(selectinload(Referral.invited_user))
            .where(Referral.id == referral_id)
        )
        return result.scalar_one_or_none()

    async def get_by_invited_user(
        self,
        invited_user_id: int,
    ) -> Referral | None:
        result = await self.session.execute(
            select(Referral).where(
                Referral.invited_user_id == invited_user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_invited_user_for_update(
        self,
        invited_user_id: int,
    ) -> Referral | None:
        result = await self.session.execute(
            select(Referral)
            .where(
                Referral.invited_user_id == invited_user_id
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_inviter_and_invited(
        self,
        inviter_user_id: int,
        invited_user_id: int,
    ) -> Referral | None:
        result = await self.session.execute(
            select(Referral).where(
                Referral.inviter_user_id == inviter_user_id,
                Referral.invited_user_id == invited_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_inviter(
        self,
        inviter_user_id: int,
    ) -> list[Referral]:
        result = await self.session.execute(
            select(Referral)
            .where(
                Referral.inviter_user_id == inviter_user_id
            )
            .order_by(Referral.id.asc())
        )
        return list(result.scalars().all())

    async def count_rewarded_by_inviter(
        self,
        inviter_user_id: int,
    ) -> int:
        result = await self.session.execute(
            select(func.count(Referral.id)).where(
                Referral.inviter_user_id == inviter_user_id,
                Referral.status == "rewarded",
            )
        )
        return int(result.scalar_one())

    async def create(
        self,
        inviter_user_id: int,
        invited_user_id: int,
    ) -> Referral:
        referral = Referral(
            inviter_user_id=inviter_user_id,
            invited_user_id=invited_user_id,
            status="pending",
        )
        self.session.add(referral)
        await self.session.flush()
        await self.session.refresh(referral)
        return referral

    async def mark_rewarded(
        self,
        referral: Referral,
        first_paid_subscription_id: int,
        rewarded_at: datetime,
    ) -> Referral:
        referral.status = "rewarded"
        referral.first_paid_subscription_id = (
            first_paid_subscription_id
        )
        referral.rewarded_at = rewarded_at
        await self.session.flush()
        await self.session.refresh(referral)
        return referral

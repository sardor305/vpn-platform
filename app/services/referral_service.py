from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.referral import Referral
from app.models.subscription import Subscription
from app.models.user_bonus import UserBonus
from app.repositories.referral_repository import ReferralRepository
from app.repositories.user_bonus_repository import UserBonusRepository
from app.repositories.user_repository import UserRepository
from app.utils.datetime import utc_now


class ReferralService:
    REFERRAL_STATUS_PENDING = "pending"
    REFERRAL_STATUS_REWARDED = "rewarded"

    BONUS_TYPE = "referral"

    BASE_REWARD_DAYS = 3
    MILESTONE_REWARD_DAYS = 7
    MILESTONE_STEP = 5

    MIN_MONTHLY_DURATION_DAYS = 30

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.referral_repository = ReferralRepository(
            session
        )
        self.user_bonus_repository = UserBonusRepository(
            session
        )
        self.user_repository = UserRepository(session)

    async def get_referral_by_invited_user(
        self,
        invited_user_id: int,
    ) -> Referral | None:
        return await self.referral_repository.get_by_invited_user(
            invited_user_id
        )

    async def bind_referral(
        self,
        inviter_user_id: int,
        invited_user_id: int,
    ) -> Referral | None:
        if inviter_user_id == invited_user_id:
            raise ValueError(
                "Self-referral is not allowed."
            )

        if (
            await self.user_repository.get_by_id(
                inviter_user_id
            )
            is None
        ):
            raise ValueError("Inviter user not found.")

        if (
            await self.user_repository.get_by_id(
                invited_user_id
            )
            is None
        ):
            raise ValueError("Invited user not found.")

        existing = (
            await self.referral_repository.get_by_invited_user(
                invited_user_id
            )
        )

        if existing is not None:
            return None

        return await self.referral_repository.create(
            inviter_user_id=inviter_user_id,
            invited_user_id=invited_user_id,
        )

    async def process_first_monthly_purchase(
        self,
        invited_user_id: int,
        subscription_id: int,
    ) -> UserBonus | None:
        referral = (
            await self.referral_repository
            .get_by_invited_user_for_update(
                invited_user_id
            )
        )

        if referral is None:
            return None

        if referral.status == self.REFERRAL_STATUS_REWARDED:
            return None

        result = await self.session.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan)
            )
            .where(
                Subscription.id == subscription_id
            )
        )

        subscription = result.scalar_one_or_none()

        if subscription is None:
            raise ValueError("Subscription not found.")

        if subscription.user_id != invited_user_id:
            raise ValueError(
                "Subscription does not belong to invited user."
            )

        if not self._is_qualifying_monthly_purchase(
            subscription
        ):
            return None

        previous_result = await self.session.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan)
            )
            .where(
                Subscription.user_id == invited_user_id,
                Subscription.id != subscription.id,
            )
            .order_by(Subscription.id.asc())
        )

        previous_subscriptions = list(
            previous_result.scalars().all()
        )

        has_previous_qualifying_purchase = any(
            self._is_qualifying_monthly_purchase(
                item
            )
            for item in previous_subscriptions
        )

        if has_previous_qualifying_purchase:
            return None

        # Different invited users can complete their first monthly
        # purchase concurrently. Serialize reward numbering for the
        # inviter so the 3/7-day milestone sequence remains correct.
        await self.session.execute(
            select(
                func.pg_advisory_xact_lock(
                    referral.inviter_user_id
                )
            )
        )

        referral_number = (
            await self.referral_repository
            .count_rewarded_by_inviter(
                inviter_user_id=referral.inviter_user_id
            )
            + 1
        )

        reward_days = self.calculate_reward_days(
            referral_number
        )

        bonus = await self.user_bonus_repository.create(
            user_id=referral.inviter_user_id,
            bonus_type=self.BONUS_TYPE,
            duration_days=reward_days,
            status="pending",
            start_date=None,
            end_date=None,
            activated_at=None,
            bonus_number=referral_number,
            referral_id=referral.id,
        )

        await self.referral_repository.mark_rewarded(
            referral=referral,
            first_paid_subscription_id=subscription.id,
            rewarded_at=utc_now(),
        )

        return bonus

    async def get_referral_number_for_next_reward(
        self,
        inviter_user_id: int,
    ) -> int:
        return (
            await self.referral_repository
            .count_rewarded_by_inviter(
                inviter_user_id
            )
            + 1
        )

    @classmethod
    def calculate_reward_days(
        cls,
        referral_number: int,
    ) -> int:
        if referral_number <= 0:
            raise ValueError(
                "Referral number must be greater than zero."
            )

        if (
            referral_number % cls.MILESTONE_STEP
            == 0
        ):
            return cls.MILESTONE_REWARD_DAYS

        return cls.BASE_REWARD_DAYS

    @classmethod
    def _is_qualifying_monthly_purchase(
        cls,
        subscription: Subscription,
    ) -> bool:
        if subscription.status not in {
            "pending",
            "active",
        }:
            return False

        if subscription.plan is None:
            return False

        duration_days = subscription.plan.duration_days

        return (
            duration_days is not None
            and duration_days
            >= cls.MIN_MONTHLY_DURATION_DAYS
        )
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_subscription import DailySubscription
from app.models.subscription import Subscription
from app.models.user_bonus import UserBonus
from app.repositories.daily_subscription_repository import (
    DailySubscriptionRepository,
)
from app.repositories.subscription_repository import (
    SubscriptionRepository,
)
from app.repositories.user_bonus_repository import UserBonusRepository
from app.utils.datetime import utc_now


@dataclass
class ServicePeriod:
    service_type: str
    item: Subscription | UserBonus | DailySubscription
    start_date: datetime | None
    end_date: datetime | None
    duration_days: int
    priority: int

    @property
    def item_id(self) -> int:
        return self.item.id

    @property
    def bonus_number(self) -> int | None:
        """Return the permanent public number for numbered bonus periods."""
        if isinstance(self.item, UserBonus):
            return self.item.bonus_number
        return None


class ServicePeriodService:
    """
    Central service-period and queue coordinator.

    This service does not process payments, create bonuses, or communicate
    with Marzban. It determines the current/next service period, activates
    queued periods, and reconciles period state.
    """

    PAID = "paid"
    PROMO = "promo"
    REFERRAL = "referral"
    ADMIN = "admin"
    DAILY = "daily"
    WELCOME = "welcome"

    PRIORITIES = {
        PAID: 10,
        PROMO: 20,
        REFERRAL: 30,
        ADMIN: 40,
        DAILY: 50,
    }

    SUPPORTED_BONUS_TYPES = {
        PROMO,
        REFERRAL,
        ADMIN,
        WELCOME,
    }

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.subscription_repository = SubscriptionRepository(session)
        self.user_bonus_repository = UserBonusRepository(session)
        self.daily_subscription_repository = (
            DailySubscriptionRepository(session)
        )

    async def get_current_service(
        self,
        user_id: int,
        now: datetime | None = None,
    ) -> ServicePeriod | None:
        current_time = now or utc_now()

        paid = await self.subscription_repository.get_active_by_user(
            user_id
        )
        bonus = await self.user_bonus_repository.get_active_by_user(
            user_id
        )
        daily = await self.daily_subscription_repository.get_active_by_user(
            user_id
        )

        active_periods: list[ServicePeriod] = []

        if paid is not None:
            active_periods.append(
                ServicePeriod(
                    service_type=self.PAID,
                    item=paid,
                    start_date=paid.start_date,
                    end_date=paid.end_date,
                    duration_days=self._subscription_duration(paid),
                    priority=self.PRIORITIES[self.PAID],
                )
            )

        if bonus is not None:
            bonus_type = bonus.bonus_type.lower()

            if bonus_type not in self.SUPPORTED_BONUS_TYPES:
                bonus_type = self.ADMIN

            priority = (
                0
                if bonus_type == self.WELCOME
                else self.PRIORITIES[bonus_type]
            )

            active_periods.append(
                ServicePeriod(
                    service_type=bonus_type,
                    item=bonus,
                    start_date=bonus.start_date,
                    end_date=bonus.end_date,
                    duration_days=bonus.duration_days,
                    priority=priority,
                )
            )

        if daily is not None:
            active_periods.append(
                ServicePeriod(
                    service_type=self.DAILY,
                    item=daily,
                    start_date=daily.start_date,
                    end_date=daily.end_date,
                    duration_days=daily.duration_days,
                    priority=self.PRIORITIES[self.DAILY],
                )
            )

        if not active_periods:
            return None

        valid_periods = [
            period
            for period in active_periods
            if (
                period.start_date is not None
                and period.end_date is not None
                and self._normalize_datetime(period.start_date) <= current_time
                and self._normalize_datetime(period.end_date) > current_time
            )
        ]

        if not valid_periods:
            return None

        valid_periods.sort(
            key=lambda period: (
                period.start_date,
                period.priority,
                period.item_id,
            )
        )

        return valid_periods[0]

    async def get_pending_queue(
        self,
        user_id: int,
        start_date: datetime | None = None,
    ) -> list[ServicePeriod]:
        """
        Return pending service periods in their execution order.

        Welcome bonuses are intentionally excluded because Welcome is a
        special one-time onboarding flow, not a normal queue item.
        """

        start = self._normalize_datetime(
            start_date or utc_now()
        )

        paid = await self.subscription_repository.get_pending_by_user(
            user_id
        )
        bonuses = await self.user_bonus_repository.get_pending_by_user(
            user_id
        )
        daily = await self.daily_subscription_repository.get_pending_by_user(
            user_id
        )

        candidates: list[ServicePeriod] = []

        for subscription in paid:
            candidates.append(
                ServicePeriod(
                    service_type=self.PAID,
                    item=subscription,
                    start_date=None,
                    end_date=None,
                    duration_days=self._subscription_duration(
                        subscription
                    ),
                    priority=self.PRIORITIES[self.PAID],
                )
            )

        for bonus in bonuses:
            bonus_type = bonus.bonus_type.lower()

            if bonus_type == self.WELCOME:
                continue

            if bonus_type not in self.SUPPORTED_BONUS_TYPES:
                continue

            candidates.append(
                ServicePeriod(
                    service_type=bonus_type,
                    item=bonus,
                    start_date=None,
                    end_date=None,
                    duration_days=self._bonus_duration(bonus),
                    priority=self.PRIORITIES[bonus_type],
                )
            )

        for daily_subscription in daily:
            candidates.append(
                ServicePeriod(
                    service_type=self.DAILY,
                    item=daily_subscription,
                    start_date=None,
                    end_date=None,
                    duration_days=self._daily_duration(
                        daily_subscription
                    ),
                    priority=self.PRIORITIES[self.DAILY],
                )
            )

        queue: list[ServicePeriod] = []
        remaining = candidates
        cursor = start

        while remaining:
            next_period = self._select_next_period(
                remaining,
                cursor,
            )

            queue.append(
                ServicePeriod(
                    service_type=next_period.service_type,
                    item=next_period.item,
                    start_date=cursor,
                    end_date=cursor
                    + timedelta(days=next_period.duration_days),
                    duration_days=next_period.duration_days,
                    priority=next_period.priority,
                )
            )

            cursor = cursor + timedelta(
                days=next_period.duration_days
            )
            remaining.remove(next_period)

        return queue

    async def get_next_service(
        self,
        user_id: int,
        start_date: datetime | None = None,
    ) -> ServicePeriod | None:
        queue = await self.get_pending_queue(
            user_id=user_id,
            start_date=start_date,
        )

        if not queue:
            return None

        return queue[0]

    async def activate_next_service(
        self,
        user_id: int,
        start_date: datetime | None = None,
    ) -> ServicePeriod | None:
        """
        Activate exactly one next period.

        An already-active service is never interrupted. If an active period
        exists, this method returns it unchanged.
        """

        current = await self.get_current_service(user_id)

        if current is not None:
            return current

        start = self._normalize_datetime(
            start_date or utc_now()
        )

        next_service = await self.get_next_service(
            user_id=user_id,
            start_date=start,
        )

        if next_service is None:
            return None

        return await self._activate_period(
            next_service,
            start,
        )

    async def reconcile_user(
        self,
        user_id: int,
        now: datetime | None = None,
    ) -> ServicePeriod | None:
        """
        Reconcile one user's service state.

        Finished active periods are marked expired. If no service remains
        active, the next queued period is activated immediately.
        """

        current_time = self._normalize_datetime(
            now or utc_now()
        )

        # Serialize all service-state mutations for the same user.
        # PostgreSQL transaction-level advisory locks are released
        # automatically when the surrounding DB transaction ends.
        await self.session.execute(
            select(func.pg_advisory_xact_lock(user_id))
        )

        await self._expire_finished_periods(
            user_id=user_id,
            now=current_time,
        )

        current = await self.get_current_service(
            user_id=user_id,
            now=current_time,
        )

        if current is not None:
            return current

        next_service = await self.activate_next_service(
            user_id=user_id,
            start_date=current_time,
        )

        if next_service is not None:
            return next_service

        welcome = await self.user_bonus_repository.get_welcome_by_user(
            user_id
        )

        if (
            welcome is not None
            and welcome.status == "pending"
        ):
            welcome_period = ServicePeriod(
                service_type=self.WELCOME,
                item=welcome,
                start_date=None,
                end_date=None,
                duration_days=welcome.duration_days,
                priority=0,
            )

            return await self._activate_period(
                welcome_period,
                current_time,
            )

        return None

    async def project_queue_end(
        self,
        user_id: int,
        start_date: datetime | None = None,
    ) -> datetime | None:
        queue = await self.get_pending_queue(
            user_id=user_id,
            start_date=start_date,
        )

        if not queue:
            return None

        return queue[-1].end_date

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:
        """Normalize a datetime to the project's UTC-aware datetime model."""
        if value.tzinfo is None:
            return value.replace(
                tzinfo=utc_now().tzinfo
            )

        return value

    @staticmethod
    def _select_next_period(
        candidates: list[ServicePeriod],
        cursor: datetime,
    ) -> ServicePeriod:
        """Select the next service using priority + FIFO order.

        Priority determines the service class. Within the same priority,
        the oldest created period is activated first, with id as a stable
        tie-breaker. No external expiry field can reorder the queue.
        """
        return min(
            candidates,
            key=lambda period: (
                period.priority,
                period.item.created_at,
                period.item_id,
            ),
        )

    @staticmethod
    def _subscription_duration(
        subscription: Subscription,
    ) -> int:
        if subscription.plan is None:
            raise ValueError(
                "Subscription plan is required for service-period calculation."
            )

        duration_days = subscription.plan.duration_days

        if duration_days <= 0:
            raise ValueError(
                "Subscription plan duration must be greater than zero."
            )

        return duration_days

    @staticmethod
    def _bonus_duration(
        bonus: UserBonus,
    ) -> int:
        if bonus.duration_days <= 0:
            raise ValueError(
                "Bonus duration must be greater than zero."
            )

        return bonus.duration_days

    @staticmethod
    def _daily_duration(
        daily: DailySubscription,
    ) -> int:
        if daily.duration_days <= 0:
            raise ValueError(
                "Daily subscription duration must be greater than zero."
            )

        return daily.duration_days

    async def _activate_period(
        self,
        period: ServicePeriod,
        start_date: datetime,
    ) -> ServicePeriod:
        start_date = self._normalize_datetime(
            start_date
        )

        end_date = start_date + timedelta(
            days=period.duration_days
        )

        if period.service_type == self.PAID:
            subscription = period.item

            if not isinstance(subscription, Subscription):
                raise TypeError(
                    "Invalid Paid service-period item."
                )

            subscription.start_date = start_date
            subscription.end_date = end_date
            subscription.status = "active"

            await self.subscription_repository.update(
                subscription
            )

            return ServicePeriod(
                service_type=self.PAID,
                item=subscription,
                start_date=start_date,
                end_date=end_date,
                duration_days=period.duration_days,
                priority=period.priority,
            )

        if period.service_type in {
            self.PROMO,
            self.REFERRAL,
            self.ADMIN,
            self.WELCOME,
        }:
            bonus = period.item

            if not isinstance(bonus, UserBonus):
                raise TypeError(
                    "Invalid bonus service-period item."
                )

            bonus.start_date = start_date
            bonus.end_date = end_date
            bonus.activated_at = utc_now()
            bonus.status = "active"

            await self.user_bonus_repository.update(
                bonus
            )

            return ServicePeriod(
                service_type=period.service_type,
                item=bonus,
                start_date=start_date,
                end_date=end_date,
                duration_days=period.duration_days,
                priority=period.priority,
            )

        if period.service_type == self.DAILY:
            daily = period.item

            if not isinstance(daily, DailySubscription):
                raise TypeError(
                    "Invalid Daily service-period item."
                )

            daily.start_date = start_date
            daily.end_date = end_date
            daily.status = "active"

            await self.daily_subscription_repository.update(
                daily
            )

            return ServicePeriod(
                service_type=self.DAILY,
                item=daily,
                start_date=start_date,
                end_date=end_date,
                duration_days=period.duration_days,
                priority=period.priority,
            )

        raise ValueError(
            f"Unsupported service type: {period.service_type}"
        )

    async def _expire_finished_periods(
        self,
        user_id: int,
        now: datetime,
    ) -> None:
        subscriptions = (
            await self.subscription_repository
            .get_expired_active_by_user(
                user_id=user_id,
                now=now,
            )
        )

        for subscription in subscriptions:
            subscription.status = "expired"

            await self.subscription_repository.update(
                subscription
            )

        bonuses = (
            await self.user_bonus_repository
            .get_expired_active_by_user(
                user_id=user_id,
                now=now,
            )
        )

        for bonus in bonuses:
            bonus.status = "expired"

            await self.user_bonus_repository.update(
                bonus
            )

        daily_subscriptions = (
            await self.daily_subscription_repository
            .get_expired_active_by_user(
                user_id=user_id,
                now=now,
            )
        )

        for daily in daily_subscriptions:
            daily.status = "expired"

            await self.daily_subscription_repository.update(
                daily
            )
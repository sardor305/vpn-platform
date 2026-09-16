from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.repositories.subscription_repository import (
    SubscriptionRepository,
)
from app.utils.datetime import utc_now


class SubscriptionService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.subscription_repository = (
            SubscriptionRepository(session)
        )

    async def get_active_subscription(
        self,
        user_id: int,
    ) -> Subscription | None:

        return await (
            self.subscription_repository
            .get_active_by_user(user_id)
        )

    async def get_latest_subscription(
        self,
        user_id: int,
    ) -> Subscription | None:

        return await (
            self.subscription_repository
            .get_latest_by_user(user_id)
        )

    async def get_pending_subscriptions(
        self,
        user_id: int,
    ) -> list[Subscription]:

        return await (
            self.subscription_repository
            .get_pending_by_user(user_id)
        )

    async def get_all_pending_subscriptions(
        self,
    ) -> list[Subscription]:

        return await (
            self.subscription_repository
            .get_all_pending()
        )

    async def get_subscription_history(
        self,
        user_id: int,
    ) -> list[Subscription]:

        return await (
            self.subscription_repository
            .get_all_by_user(user_id)
        )

    async def get_subscription_history_paginated(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[Subscription], int]:

        return await (
            self.subscription_repository
            .get_all_by_user_paginated(
                user_id=user_id,
                page=page,
                page_size=page_size,
            )
        )

    async def get_all_subscription_history_paginated(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Subscription], int]:

        return await (
            self.subscription_repository
            .get_all_paginated(
                page=page,
                page_size=page_size,
            )
        )

    async def get_all_active_subscriptions(
        self,
    ) -> list[Subscription]:

        return await (
            self.subscription_repository
            .get_all_active()
        )

    async def get_all_active_for_expiry_check(
        self,
    ) -> list[Subscription]:

        return await (
            self.subscription_repository
            .get_all_active_for_expiry_check()
        )

    async def create_subscription(
        self,
        user_id: int,
        plan_id: int,
        duration_days: int,
    ) -> Subscription:

        if duration_days <= 0:
            raise ValueError(
                "Subscription duration must be greater than zero."
            )

        return await self.subscription_repository.create(
            user_id=user_id,
            plan_id=plan_id,
            start_date=None,
            end_date=None,
            status="pending",
        )

    async def activate_subscription(
        self,
        subscription: Subscription,
        start_date=None,
    ) -> Subscription:

        if subscription.status != "pending":
            raise ValueError(
                "Only pending subscriptions can be activated."
            )

        if subscription.start_date is not None:
            raise ValueError(
                "Subscription already has a start date."
            )

        if subscription.end_date is not None:
            raise ValueError(
                "Subscription already has an end date."
            )

        start = start_date or utc_now()

        if start.tzinfo is None:
            start = start.replace(tzinfo=utc_now().tzinfo)

        if subscription.plan is None:
            raise ValueError(
                "Subscription plan is required to activate it."
            )

        end = start + timedelta(
            days=subscription.plan.duration_days
        )

        subscription.start_date = start
        subscription.end_date = end
        subscription.status = "active"

        return await self.subscription_repository.update(
            subscription
        )

    async def change_plan(
        self,
        subscription: Subscription,
        plan_id: int,
    ) -> Subscription:

        if subscription.status != "active":
            raise ValueError(
                "Only active subscriptions can change plan."
            )

        subscription.plan_id = plan_id

        return await self.subscription_repository.update(
            subscription
        )

    async def extend_subscription(
        self,
        subscription: Subscription,
        duration_days: int,
    ) -> Subscription:

        if duration_days <= 0:
            raise ValueError(
                "Extension duration must be greater than zero."
            )

        if subscription.status != "active":
            raise ValueError(
                "Only active subscriptions can be extended."
            )

        if subscription.end_date is None:
            raise ValueError(
                "Active subscription must have an end date."
            )

        subscription.end_date = (
            subscription.end_date
            + timedelta(days=duration_days)
        )

        return await self.subscription_repository.update(
            subscription
        )

    async def adjust_subscription_duration(
        self,
        subscription: Subscription,
        days: int,
    ) -> Subscription:

        if subscription.status != "active":
            raise ValueError(
                "Only active subscriptions can be adjusted."
            )

        if subscription.end_date is None:
            raise ValueError(
                "Active subscription must have an end date."
            )

        new_end_date = (
            subscription.end_date
            + timedelta(days=days)
        )

        now = utc_now()

        if new_end_date <= now:
            raise ValueError(
                "Obuna muddatini bundan ortiq "
                "qisqartirish mumkin emas."
            )

        subscription.end_date = new_end_date

        return await self.subscription_repository.update(
            subscription
        )